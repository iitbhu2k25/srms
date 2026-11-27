# Sewage treatment plants (media/STP/STP.shp). The attribute table came from Excel, so values are cleaned here:
# numbers stored as text are parsed, 0 for an actual/design value means "not reported" (NULL), and the
# tapped-drain lists (mixed commas / spaces, duplicates) become integer arrays.
import re

import os
import sys

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiLineString, MultiPolygon
import shapely

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_connection import MEDIA_DIR, engine, table_has_rows  # noqa: E402


def to_2d(geom):
    """Drop Z values (the river shapefile is 3-D)."""
    return shapely.force_2d(geom)


TABLE_NAME = 'stps'
SHP_FILE = os.path.join(MEDIA_DIR, "STP", "STP.shp")
QUALITY = ["BOD", "COD", "TSS", "pH", "FC"]
TEXT_FIXES = {"Varansi": "Varanasi"}


def number(series, zero_is_missing=True):
    v = pd.to_numeric(series, errors="coerce")
    return v.where(v != 0) if zero_is_missing else v


def drain_codes(text):
    """PostgreSQL array literal, e.g. '{220,228}' (COPY into an integer[] column)."""
    if not isinstance(text, str) or not text.strip():
        return None
    return "{" + ",".join(str(c) for c in sorted({int(c) for c in re.findall(r"\d+", text)})) + "}"


def status(text):
    if not isinstance(text, str):
        return None
    text = text.strip()
    return "Compliant" if text.lower().startswith("compli") else text   # e.g. "Compli+C17:N17" (Excel artifact)


def load():
    try:
        if table_has_rows(TABLE_NAME):
            print(f"{TABLE_NAME} already has data, skipping.")
            return
        gdf = gpd.read_file(SHP_FILE).to_crs(4326)
        geom = gdf.geometry.apply(to_2d).apply(lambda g: MultiPolygon([g]) if g.geom_type == "Polygon" else g)
        out = pd.DataFrame({
            "stp_code": gdf["stp_code"].astype(int),
            "name": gdf["Name"].str.strip(),
            "status": gdf["STP_Status"].apply(status),
            "maintained_by": gdf["STP_Mainta"].str.strip(),
            "stp_type": gdf["STP_Type"].str.strip(),
            "capacity_mld": number(gdf["Capacity"]),
            "utilized_mld": number(gdf["Utilize"], zero_is_missing=False),
            "remarks": gdf["Remarks"].str.strip(),
            "tapped_drains": gdf["Tapped_dra"].apply(drain_codes),
            "river_name": gdf["River_name"].str.strip().str.title(),
            "district": gdf["District"].str.strip().replace(TEXT_FIXES),
        })
        for q in QUALITY:
            out[f"{q.lower()}_actual"] = number(gdf[f"{q}_Actual"])
            out[f"{q.lower()}_design"] = number(gdf[f"{q}_Design"])
        # Point for markers: the attribute coordinates, falling back to the polygon centroid.
        centroid = geom.to_crs(32644).centroid.to_crs(4326)
        out["lat"] = number(gdf["Latitude"]).fillna(centroid.y).round(6)
        out["lon"] = number(gdf["Longitude"]).fillna(centroid.x).round(6)
        out = gpd.GeoDataFrame(out, geometry=geom.values, crs=4326).rename_geometry("geom")
        out.to_postgis(TABLE_NAME, engine, if_exists='append', index=False)
        print(f"{len(out)} STPs ({out['capacity_mld'].sum():,.0f} MLD capacity) inserted into {TABLE_NAME}.")
    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    load()
