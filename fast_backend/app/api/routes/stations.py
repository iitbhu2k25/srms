from fastapi import APIRouter, Query

from app.api.schema.station_schema import ParameterSeries, StationForecast, StationLatest
from app.api.service.forecast_svc import forecast_svc
from app.api.service.station_svc import station_svc
from app.database.config.dependency import db_read

router = APIRouter()


@router.get("", response_model=list[StationLatest])
async def get_stations(db: db_read):
    """All river stations with their latest reading, status and health index."""
    return await station_svc.list_latest(db)


@router.get("/{station_code}", response_model=StationLatest)
async def get_station(db: db_read, station_code: str):
    return await station_svc.get_latest(db, station_code)


@router.get("/{station_code}/series", response_model=list[ParameterSeries])
async def get_series(
    db: db_read,
    station_code: str,
    parameters: str = Query("do,ph,turbidity", description="Comma-separated parameter keys"),
    hours: int = Query(24, ge=1, le=2160),
):
    keys = [p.strip() for p in parameters.split(",") if p.strip()]
    return await station_svc.get_series(db, station_code, keys, hours)


@router.get("/{station_code}/forecast", response_model=StationForecast)
async def get_forecast(db: db_read, station_code: str):
    """3-day faecal coliform forecast (placeholder for the AI bacterial forecasting model)."""
    return await forecast_svc.get_forecast(db, station_code)
