from fastapi import APIRouter

from app.api.schema.dashboard_schema import IngestAck, IngestReading
from app.api.service.ingest_svc import ingest_svc
from app.database.config.dependency import db_write

router = APIRouter()


@router.post("/readings", response_model=IngestAck)
async def ingest_readings(db: db_write, payload: IngestReading):
    """Endpoint for IoT stations / the ESP32 water-quality unit to push readings (device_id = stations.device_id)."""
    return await ingest_svc.ingest(db, payload.model_dump())
