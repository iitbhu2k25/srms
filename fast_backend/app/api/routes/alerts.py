from fastapi import APIRouter

from app.api.schema.alert_schema import Alert
from app.api.service.alert_svc import alert_svc
from app.database.config.dependency import db_read

router = APIRouter()


@router.get("", response_model=list[Alert])
async def get_alerts(db: db_read, status: str | None = None, severity: str | None = None, station_id: str | None = None):
    return await alert_svc.list_alerts(db, status, severity, station_id)
