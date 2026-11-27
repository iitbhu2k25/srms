# Places the dummy seed points on the real river network (rivers table, loaded from media/Rivers):
#   - stations and boat waypoints are snapped onto the Varuna; chainage_km is recomputed from the real line
#   - the two confluence stations move to the real Morwa / Basuhi confluences (wells & TEM transects follow)
#   - outfall hotspots are placed on real untapped drains (drains table, media/Drains)
# Rewrites media/data/*.csv + boat_mission.json (the seed source of truth) and updates the matching rows.
# Usage (from fast_backend/, after the GIS loaders ran): python -m script.tools.snap_seed_to_rivers
import json
import os

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import LineString, Point
from sqlalchemy import text

from script.database.db_connection import DATA_DIR, engine

UTM = 32644                      # UTM 44N (metres)
UPSTREAM_REFERENCE_KM = 4.0      # VR-01 sits this far below the origin
WELL_OFFSET_M = 400              # floodplain wells: distance from the river
OFF_BANK_M = 120                 # encroachment / solid-waste hotspots: distance from the river
OUTFALL_DRAINS = {"H-01": 58, "H-02": 41, "H-03": 61}   # largest untapped urban Varuna drains

to_utm = lambda gs: gpd.GeoSeries(gs, crs=4326).to_crs(UTM)  # noqa: E731


def river(name: str):
    return gpd.read_postgis(text("SELECT geom FROM rivers WHERE name = :n"), engine, params={"n": name},
                            geom_col="geom").to_crs(UTM).geometry.iloc[0]


def single_line(multi) -> LineString:
    """Chain the parts of a MultiLineString end-to-start (small gaps bridged), from the western (source) end."""
    parts = [list(p.coords) for p in getattr(multi, "geoms", [multi])]
    # orient each part west -> east (the Varuna flows eastwards to the Ganga)
    parts = [c if c[0][0] <= c[-1][0] else c[::-1] for c in parts]
    parts.sort(key=lambda c: c[0][0])
    chain = parts.pop(0)
    while parts:
        nxt = min(parts, key=lambda c: Point(c[0]).distance(Point(chain[-1])))
        parts.remove(nxt)
        chain += nxt
    return LineString(chain)


def latlon(pt_utm) -> tuple[float, float]:
    p = gpd.GeoSeries([pt_utm], crs=UTM).to_crs(4326).iloc[0]
    return round(float(p.y), 6), round(float(p.x), 6)


def offset_from(line: LineString, pt_utm: Point, metres: float) -> Point:
    """Point `metres` away from the river, perpendicular to it at pt_utm (left bank)."""
    d = line.project(pt_utm)
    a, b = line.interpolate(max(0, d - 50)), line.interpolate(min(line.length, d + 50))
    dx, dy = b.x - a.x, b.y - a.y
    n = (dx * dx + dy * dy) ** 0.5 or 1
    return Point(pt_utm.x - dy / n * metres, pt_utm.y + dx / n * metres)


def main():
    varuna = single_line(river("Varuna"))
    snap = lambda lat, lon: varuna.interpolate(varuna.project(to_utm([Point(lon, lat)]).iloc[0]))  # noqa: E731
    km = lambda pt: round(varuna.project(pt) / 1000, 1)  # noqa: E731
    confluence = {name: varuna.interpolate(varuna.project(Point(river(name).geoms[-1].coords[-1])))
                  for name in ("Morwa", "Basuhi")}
    print(f"Varuna length {varuna.length / 1000:.1f} km; confluences: "
          + ", ".join(f"{k} at km {km(v)}" for k, v in confluence.items()))

    # ---- stations ----
    st = pd.read_csv(os.path.join(DATA_DIR, "stations.csv"))
    st["chainage_km"] = st["chainage_km"].astype(float)
    pts = {}
    for i, s in st.iterrows():
        if s.station_code == "VR-01":
            p = varuna.interpolate(UPSTREAM_REFERENCE_KM * 1000)
        elif s.station_code == "VR-02":
            p = confluence["Basuhi"]
        elif s.station_code == "VR-03":
            p = confluence["Morwa"]
        else:
            p = snap(s.lat, s.lon)
        pts[s.station_code] = p
        st.loc[i, ["lat", "lon"]] = latlon(p)
        st.loc[i, "chainage_km"] = km(p)
    st.to_csv(os.path.join(DATA_DIR, "stations.csv"), index=False)

    # ---- wells: floodplain of the paired station ----
    wl = pd.read_csv(os.path.join(DATA_DIR, "wells.csv"))
    for i, w in wl.iterrows():
        wl.loc[i, ["lat", "lon"]] = latlon(offset_from(varuna, pts[w.paired_station], WELL_OFFSET_M))
    wl.to_csv(os.path.join(DATA_DIR, "wells.csv"), index=False)

    # ---- TEM transects: perpendicular to the river, centred on their station ----
    tm = pd.read_csv(os.path.join(DATA_DIR, "tem_transects.csv"))
    for i, t in tm.iterrows():
        c = pts[t.station_code]
        tm.loc[i, ["start_lat", "start_lon"]] = latlon(offset_from(varuna, c, t.length_m / 2))
        tm.loc[i, ["end_lat", "end_lon"]] = latlon(offset_from(varuna, c, -t.length_m / 2))
    tm.to_csv(os.path.join(DATA_DIR, "tem_transects.csv"), index=False)

    # ---- hotspots ----
    hs = pd.read_csv(os.path.join(DATA_DIR, "hotspots.csv"))
    drains = pd.read_sql(text("SELECT drain_code, name, discharge, lat, lon FROM drains WHERE river_name = 'Varuna'"),
                         engine).set_index("drain_code")
    for i, h in hs.iterrows():
        if h.hotspot_code in OUTFALL_DRAINS:
            d = drains.loc[OUTFALL_DRAINS[h.hotspot_code]]
            hs.loc[i, ["lat", "lon"]] = (float(d.lat), float(d.lon))
            label = d["name"] if isinstance(d["name"], str) else f"Drain {OUTFALL_DRAINS[h.hotspot_code]}"
            observed = h.detail.split(" — ")[-1].split(";")[0]          # idempotent on re-runs
            hs.loc[i, "detail"] = f"{label}: untapped, {d.discharge:g} MLD — {observed}"
        elif h.hotspot_code == "H-08":          # algal bloom below the Morwa confluence
            hs.loc[i, ["lat", "lon"]] = latlon(varuna.interpolate(varuna.project(confluence["Morwa"]) + 1500))
        else:
            p = snap(h.lat, h.lon)
            if h.hotspot_type in ("Encroachment", "Solid waste"):
                p = offset_from(varuna, p, OFF_BANK_M)
            hs.loc[i, ["lat", "lon"]] = latlon(p)
    hs.to_csv(os.path.join(DATA_DIR, "hotspots.csv"), index=False)

    # ---- boat mission ----
    path = os.path.join(DATA_DIR, "boat_mission.json")
    mission = json.load(open(path, encoding="utf-8"))
    for w in mission["waypoints"]:
        w["lat"], w["lon"] = latlon(snap(w["lat"], w["lon"]))
    json.dump(mission, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    # ---- update the database rows ----
    st, wl, tm, hs = (df.astype({c: float for c in df.columns if df[c].dtype.kind == "f"}) for df in (st, wl, tm, hs))
    with engine.begin() as con:
        for s in st.itertuples():
            con.execute(text("UPDATE stations SET lat=:lat, lon=:lon, chainage_km=:km WHERE station_code=:c"),
                        {"lat": s.lat, "lon": s.lon, "km": s.chainage_km, "c": s.station_code})
            con.execute(text("UPDATE samples SET lat=:lat, lon=:lon WHERE station_code=:c AND matrix <> 'groundwater'"),
                        {"lat": s.lat, "lon": s.lon, "c": s.station_code})
            con.execute(text("UPDATE cross_sections SET chainage_km=:km WHERE station_code=:c"),
                        {"km": s.chainage_km, "c": s.station_code})
        for w in wl.itertuples():
            con.execute(text("UPDATE wells SET lat=:lat, lon=:lon WHERE well_code=:c"),
                        {"lat": w.lat, "lon": w.lon, "c": w.well_code})
        gw03 = wl[wl.well_code == "GW-03"].iloc[0]
        con.execute(text("UPDATE samples SET lat=:lat, lon=:lon WHERE matrix = 'groundwater'"),
                    {"lat": float(gw03.lat), "lon": float(gw03.lon)})
        for t in tm.itertuples():
            con.execute(text("UPDATE tem_transects SET start_lat=:a, start_lon=:b, end_lat=:c, end_lon=:d "
                             "WHERE transect_code=:t"),
                        {"a": t.start_lat, "b": t.start_lon, "c": t.end_lat, "d": t.end_lon, "t": t.transect_code})
        for h in hs.itertuples():
            con.execute(text("UPDATE hotspots SET lat=:lat, lon=:lon, detail=:d WHERE hotspot_code=:c"),
                        {"lat": h.lat, "lon": h.lon, "d": h.detail, "c": h.hotspot_code})
        for w in mission["waypoints"]:
            con.execute(text("UPDATE boat_waypoints SET lat=:lat, lon=:lon WHERE mission_code=:m AND seq=:s"),
                        {"lat": w["lat"], "lon": w["lon"], "m": mission["mission_code"], "s": w["seq"]})

    for s in st.sort_values("chainage_km").itertuples():
        print(f"  {s.station_code} {s.name:<28} km {s.chainage_km:>6}  ({s.lat}, {s.lon})")


if __name__ == "__main__":
    main()
