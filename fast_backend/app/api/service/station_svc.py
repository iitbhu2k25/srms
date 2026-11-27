from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.service.health_svc import health_svc
from app.conf.settings import settings
from app.database.crud.reading.async_crud import Reading_crud
from app.database.crud.station.async_crud import Station_crud
from app.database.models import READING_COLUMNS

PUBLIC_FIELDS = ("name", "lat", "lon", "reach", "district", "chainage_km", "telemetry", "installed")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _station_out(s: dict, latest: dict | None, parameters: list[dict]) -> dict:
    reading = {k: latest[k] for k in READING_COLUMNS if latest and latest.get(k) is not None}
    rhi = health_svc.health_index(reading) if reading else 0.0
    offline = latest is None or _now() - latest["ts"] > timedelta(minutes=settings.OFFLINE_AFTER_MINUTES)
    return {
        "id": s["station_code"],
        **{k: s[k] for k in PUBLIC_FIELDS},
        "installed": s["installed"].isoformat(),
        "status": "offline" if offline else health_svc.category(rhi),
        "health_index": rhi,
        "last_seen": latest["ts"].isoformat() if latest else None,
        "battery_v": latest.get("battery_v") if latest else None,
        "signal_dbm": latest.get("signal_dbm") if latest else None,
        "reading": reading,
        "exceedances": health_svc.exceedances(reading, parameters),
    }


class station_svc:

    async def get_station_or_404(db: AsyncSession, station_code: str) -> dict:
        s = await Station_crud(db).get_station(station_code)
        if not s:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Station {station_code} not found")
        return s

    async def get_parameters(db: AsyncSession) -> dict:
        return {p["key"]: {"label": p["label"], "unit": p["unit"], "min": p["min_limit"], "max": p["max_limit"],
                           "group": p["group_name"]} for p in await Station_crud(db).get_parameters()}

    async def list_latest(db: AsyncSession) -> list[dict]:
        crud = Station_crud(db)
        stations, parameters = await crud.get_stations(), await crud.get_parameters()
        latest = {r["station_code"]: r for r in await Reading_crud(db).latest_per_station()}
        return [_station_out(s, latest.get(s["station_code"]), parameters) for s in stations]

    async def get_latest(db: AsyncSession, station_code: str) -> dict:
        s = await station_svc.get_station_or_404(db, station_code)
        parameters = await Station_crud(db).get_parameters()
        return _station_out(s, await Reading_crud(db).latest(station_code), parameters)

    async def get_series(db: AsyncSession, station_code: str, parameters: list[str], hours: int) -> list[dict]:
        await station_svc.get_station_or_404(db, station_code)
        meta = {p["key"]: p for p in await Station_crud(db).get_parameters()}
        unknown = [p for p in parameters if p not in meta or p not in READING_COLUMNS]
        if unknown:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown parameter(s): {', '.join(unknown)}")
        # keep responses around ~400 points: raw 15-min up to 4 days, hourly up to 2 weeks, then 6-hourly
        bucket = 15 if hours <= 96 else 60 if hours <= 336 else 360
        last = await Reading_crud(db).latest(station_code)
        end = last["ts"] if last else _now()
        rows = await Reading_crud(db).series(station_code, parameters, end - timedelta(hours=hours), end, bucket)
        out = []
        for p in parameters:
            m = meta[p]
            out.append({
                "station_id": station_code, "parameter": p, "label": m["label"], "unit": m["unit"],
                "limit_min": m["min_limit"], "limit_max": m["max_limit"],
                "points": [{"t": r["t"].isoformat(), "v": None if r[p] is None else float(r[p])} for r in rows],
            })
        return out
