from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.groundwater.async_crud import Groundwater_crud
from app.database.crud.reading.async_crud import Reading_crud

# Dummy datum: river bed taken 10 m below ground at each paired site, so both heads share one reference.
RIVER_BED_DEPTH_M = 10.0


def _exchange(depth_to_water: float, river_level: float | None, zone: str) -> tuple[float | None, str]:
    if river_level is None:
        return None, "unknown"
    diff = round((RIVER_BED_DEPTH_M - depth_to_water) - river_level, 2)
    if diff < -2 and "disconnected" in zone.lower():
        return diff, "disconnected"
    return diff, "gaining" if diff > 0 else "losing"


class groundwater_svc:

    async def get_wells(db: AsyncSession) -> list[dict]:
        crud = Groundwater_crud(db)
        wells, latest = await crud.get_wells(), await crud.latest_per_well()
        river = await Reading_crud(db).latest_water_level_per_station()
        out = []
        for w in wells:
            gw = latest.get(w["well_code"])
            level = river.get(w["paired_station"])
            diff, state = _exchange(gw["depth_to_water_m"], level, w["zone"]) if gw else (None, "unknown")
            out.append({
                "id": w["well_code"], "name": w["name"], "lat": w["lat"], "lon": w["lon"],
                "paired_station": w["paired_station"], "depth_m": w["depth_m"], "zone": w["zone"],
                "latest": {k: gw[k] for k in ("depth_to_water_m", "ec", "temperature")} if gw else {},
                "river_level_m": level, "head_difference_m": diff, "exchange": state,
            })
        return out

    async def get_well_series(db: AsyncSession, well_code: str, days: int) -> dict:
        well = await Groundwater_crud(db).get_well(well_code)
        if not well:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Well {well_code} not found")
        start = datetime.now(timezone.utc) - timedelta(days=days)
        rows = await Groundwater_crud(db).series_with_river(well, start, 6 if days <= 30 else 24)
        points = []
        for r in rows:
            diff, _ = _exchange(r["depth_to_water_m"], r["river_level_m"], well["zone"])
            points.append({
                "t": r["t"].isoformat(), "depth_to_water_m": round(r["depth_to_water_m"], 2), "ec": round(r["ec"]),
                "temperature": round(r["temperature"], 2),
                "river_level_m": None if r["river_level_m"] is None else round(r["river_level_m"], 2),
                "head_difference_m": diff,
            })
        return {"well_id": well_code, "points": points}
