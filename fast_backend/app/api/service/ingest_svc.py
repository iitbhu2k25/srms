"""Readings pushed by IoT stations / the ESP32 water-quality unit (POST /api/ingest/readings)."""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.reading.async_crud import Reading_crud
from app.database.crud.station.async_crud import Station_crud
from app.database.models import READING_COLUMNS

DEVICE_KEYS = ("battery_v", "signal_dbm")


class ingest_svc:

    async def ingest(db: AsyncSession, payload: dict) -> dict:
        crud = Station_crud(db)
        station = await crud.get_by_device(payload["device_id"])
        if not station:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown device {payload['device_id']}")
        limits = {p["key"]: p for p in await crud.get_parameters()}
        ts = datetime.fromisoformat(payload["timestamp"]) if payload.get("timestamp") else datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        row, flags = {"station_code": station["station_code"], "ts": ts, "source": "device"}, []
        for k, v in payload["readings"].items():
            if k in READING_COLUMNS or k in DEVICE_KEYS:
                row[k] = v
                p = limits.get(k)
                if p and ((p["min_limit"] is not None and v < p["min_limit"]) or (p["max_limit"] is not None and v > p["max_limit"])):
                    flags.append(f"{k} outside permissible range")
            else:
                flags.append(f"unknown parameter '{k}' ignored")
        await Reading_crud(db).upsert_many([row], ["station_code", "ts"])
        return {"accepted": True, "device_id": payload["device_id"], "station_id": station["station_code"],
                "timestamp": ts.isoformat(), "stored": len(row) - 3, "flags": flags}
