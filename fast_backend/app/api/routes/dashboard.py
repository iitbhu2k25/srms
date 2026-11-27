from fastapi import APIRouter, Query

from app.api.schema.dashboard_schema import HealthHistoryPoint, Overview
from app.api.service.dashboard_svc import dashboard_svc
from app.api.service.station_svc import station_svc
from app.database.config.dependency import db_read

router = APIRouter()


@router.get("/overview", response_model=Overview)
async def get_overview(db: db_read):
    """KPIs for the dashboard home page and the river centre-line."""
    return await dashboard_svc.get_overview(db)


@router.get("/health-index/history", response_model=list[HealthHistoryPoint])
async def get_health_history(db: db_read, months: int = Query(12, ge=1, le=36)):
    """Monthly River Health Index, basin average and per station."""
    return await dashboard_svc.get_health_history(db, months)


@router.get("/parameters")
async def get_parameters(db: db_read):
    """Parameter dictionary: label, unit, permissible limits, group."""
    return await station_svc.get_parameters(db)
