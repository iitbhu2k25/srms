"""
Live dummy-data simulator (settings.SIMULATE_LIVE).

Every SIMULATOR_TICK_SECONDS it appends the missing 15-min readings of active stations (and hourly well
readings) up to now, so the dashboard keeps moving. Inserts are ON CONFLICT DO NOTHING, so running in several
gunicorn workers at once is harmless. Disable it once real devices push data.
"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import ProgrammingError

from app.api.service.simulator_svc import generator as g
from app.conf.logging.applog import logger
from app.conf.settings import settings
from app.database.config.dependency import write_session_ctx
from app.database.crud.base.async_base import CrudBase
from app.database.crud.groundwater.async_crud import Groundwater_crud
from app.database.crud.reading.async_crud import Reading_crud
from app.database.crud.station.async_crud import Station_crud
from app.database.models import WellReading

MAX_BACKFILL = timedelta(days=7)  # never generate more than this in one go (seed history comes from script/)


def _missing(last: datetime | None, now: datetime, step: timedelta) -> list[datetime]:
    start = max(last + step, now - MAX_BACKFILL) if last else now - timedelta(hours=1)
    start = g.floor_to_interval(start, int(step.total_seconds() // 60) if step < timedelta(hours=1) else 60)
    out, ts = [], start
    while ts <= now:
        if last is None or ts > last:
            out.append(ts)
        ts += step
    return out


async def tick() -> int:
    now = datetime.now(timezone.utc)
    added = 0
    async with write_session_ctx() as db:
        stations = [s for s in await Station_crud(db).get_stations() if s["is_active"]]
        last = await Reading_crud(db).last_ts_per_station()
        rows = []
        for s in stations:
            for ts in _missing(last.get(s["station_code"]), g.floor_to_interval(now), timedelta(minutes=g.INTERVAL_MIN)):
                rows.append({"station_code": s["station_code"], "ts": ts, "source": "simulator",
                             **g.river_reading(s["station_code"], s["profile"], ts)})
        for i in range(0, len(rows), 2000):
            await Reading_crud(db).insert_ignore_many(rows[i:i + 2000], ["station_code", "ts"])
        added += len(rows)

        gw = Groundwater_crud(db)
        wells, wlast = await gw.get_wells(), await gw.last_ts_per_well()
        wrows = []
        hour = now.replace(minute=0, second=0, microsecond=0)
        for w in wells:
            for ts in _missing(wlast.get(w["well_code"]), hour, timedelta(hours=1)):
                wrows.append({"well_code": w["well_code"], "ts": ts, **g.well_reading(w["well_code"], ts)})
        await CrudBase(db, WellReading).insert_ignore_many(wrows, ["well_code", "ts"])
        added += len(wrows)
    return added


async def run_forever():
    logger.info("Live simulator started (tick %ss)", settings.SIMULATOR_TICK_SECONDS)
    while True:
        try:
            n = await tick()
            if n:
                logger.info("Simulator added %s readings", n)
        except ProgrammingError:
            logger.warning("Simulator waiting: tables not created yet — run ./fast_backend/start.sh")
        except Exception:  # never let the loop die
            logger.exception("Simulator tick failed")
        await asyncio.sleep(settings.SIMULATOR_TICK_SECONDS)
