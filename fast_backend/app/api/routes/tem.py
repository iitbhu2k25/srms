from fastapi import APIRouter

from app.api.schema.survey_schema import TemSection, TemTransect
from app.api.service.survey_svc import survey_svc
from app.database.config.dependency import db_read

router = APIRouter()


@router.get("/transects", response_model=list[TemTransect])
async def get_transects(db: db_read):
    return await survey_svc.get_transects(db)


@router.get("/transects/{transect_code}/section", response_model=TemSection)
async def get_section(db: db_read, transect_code: str):
    """2-D resistivity section (depth × distance) from stitched 1-D inversions."""
    return await survey_svc.get_section(db, transect_code)
