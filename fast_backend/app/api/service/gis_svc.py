import json

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.service.station_svc import station_svc
from app.database.crud.spatial.async_crud import Spatial_crud

# Effluent parameters where "actual > design" is a non-compliance (pH is a range, checked separately).
DESIGN_LIMITS = ("bod", "cod", "tss", "fc")


def _stp_out(s: dict) -> dict:
    cap, used = s["capacity_mld"], s["utilized_mld"]
    pct = round(used / cap * 100, 1) if cap and used is not None else None
    exceed = [p for p in DESIGN_LIMITS
              if s[f"{p}_actual"] is not None and s[f"{p}_design"] is not None and s[f"{p}_actual"] > s[f"{p}_design"]]
    if s["ph_actual"] is not None and not 6.5 <= s["ph_actual"] <= (s["ph_design"] or 9.0):
        exceed.append("ph")
    return {**s, "footprint": json.loads(s["footprint"]), "tapped_drains": s["tapped_drains"] or [],
            "utilization_pct": pct, "overloaded": pct is not None and pct > 100, "exceedances": exceed}


class gis_svc:

    async def get_boundary(db: AsyncSession) -> dict:
        b = await Spatial_crud(db).get_boundary()
        if not b:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Basin boundary not loaded")
        return {"type": "Feature", "geometry": json.loads(b["geom"]),
                "properties": {"name": b["name"], "area_km2": round(b["area_km2"], 1)}}

    async def get_rivers(db: AsyncSession) -> dict:
        return {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": json.loads(r["geom"]),
             "properties": {"river_code": r["river_code"], "name": r["name"], "length_km": r["length_km"]}}
            for r in await Spatial_crud(db).get_rivers()]}

    async def get_drains(db: AsyncSession, river: str | None, tapping: str | None) -> list[dict]:
        return await Spatial_crud(db).get_drains(river, tapping)

    async def get_drain_summary(db: AsyncSession) -> list[dict]:
        return [{**d, "discharge_total": float(d["discharge_total"]), "discharge_untreated": float(d["discharge_untreated"])}
                for d in await Spatial_crud(db).drain_summary()]

    async def get_stps(db: AsyncSession) -> list[dict]:
        return [_stp_out(s) for s in await Spatial_crud(db).get_stps()]

    async def get_nearby(db: AsyncSession, station_code: str, radius_m: float) -> dict:
        st = await station_svc.get_station_or_404(db, station_code)
        near = await Spatial_crud(db).near_station(st["lat"], st["lon"], radius_m)
        for d in near["drains"] + near["nearest_stps"]:
            d["distance_m"] = round(d["distance_m"])
        open_drains = [d for d in near["drains"] if d["tapping_status"] != "Tapped"]
        return {
            "station_id": station_code, "radius_m": radius_m, "drains": near["drains"],
            "untapped": len(open_drains),
            "discharge_untreated": round(sum(d["discharge"] or 0 for d in open_drains), 1),
            "nearest_stps": near["nearest_stps"],
        }
