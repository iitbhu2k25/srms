from fastapi import APIRouter, Query

from app.api.schema.station_schema import Well, WellSeries
from app.api.service.groundwater_svc import groundwater_svc
from app.database.config.dependency import db_read

router = APIRouter()


@router.get("/wells", response_model=list[Well])
async def get_wells(db: db_read):
    """TEM-sited groundwater loggers with river–aquifer exchange state."""
    return await groundwater_svc.get_wells(db)


@router.get("/wells/{well_code}/series", response_model=WellSeries)
async def get_well_series(db: db_read, well_code: str, days: int = Query(30, ge=1, le=365)):
    return await groundwater_svc.get_well_series(db, well_code, days)
