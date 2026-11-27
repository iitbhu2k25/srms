from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.survey.async_crud import Survey_crud


class survey_svc:

    async def get_transects(db: AsyncSession) -> list[dict]:
        return [{"id": t["transect_code"], "name": t["name"], "survey_date": t["survey_date"].isoformat(),
                 "length_m": t["length_m"], "start": [t["start_lat"], t["start_lon"]], "end": [t["end_lat"], t["end_lon"]],
                 "station": t["station_code"], "finding": t["finding"]} for t in await Survey_crud(db).get_transects()]

    async def get_section(db: AsyncSession, transect_code: str) -> dict:
        s = await Survey_crud(db).get_section(transect_code)
        if not s:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transect {transect_code} not found")
        return {"transect_id": s["transect_code"], "distances_m": s["distances_m"], "depths_m": s["depths_m"],
                "resistivity": s["resistivity"], "interpretation": s["interpretation"]}

    async def get_surveys(db: AsyncSession) -> list[dict]:
        return [{"id": s["survey_code"], "name": s["name"], "date": s["survey_date"].isoformat(), "season": s["season"],
                 "platform": s["platform"], "area_km2": s["area_km2"], "gsd_cm": s["gsd_cm"]}
                for s in await Survey_crud(db).get_surveys()]

    async def get_hotspots(db: AsyncSession, survey_code: str | None, hotspot_type: str | None) -> list[dict]:
        return [{"id": h["hotspot_code"], "type": h["hotspot_type"], "lat": h["lat"], "lon": h["lon"],
                 "survey": h["survey_code"], "detail": h["detail"], "severity": h["severity"]}
                for h in await Survey_crud(db).get_hotspots(survey_code, hotspot_type)]

    async def get_cross_sections(db: AsyncSession) -> list[dict]:
        return await Survey_crud(db).get_cross_sections()
