from fastapi import APIRouter

from app.api.schema.survey_schema import CrossSection, Hotspot, Survey
from app.api.service.survey_svc import survey_svc
from app.database.config.dependency import db_read

router = APIRouter()


@router.get("", response_model=list[Survey])
async def get_surveys(db: db_read):
    return await survey_svc.get_surveys(db)


@router.get("/hotspots", response_model=list[Hotspot])
async def get_hotspots(db: db_read, survey: str | None = None, type: str | None = None):
    return await survey_svc.get_hotspots(db, survey, type)


@router.get("/cross-sections", response_model=list[CrossSection])
async def get_cross_sections(db: db_read):
    return await survey_svc.get_cross_sections(db)
