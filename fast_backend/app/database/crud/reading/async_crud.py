from datetime import datetime

from sqlalchemy import Numeric, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.base.async_base import CrudBase
from app.database.models import READING_COLUMNS, RiverReading

VALUE_COLUMNS = [getattr(RiverReading, c) for c in READING_COLUMNS]
DEVICE_COLUMNS = [RiverReading.battery_v, RiverReading.signal_dbm]


class Reading_crud(CrudBase):

    def __init__(self, db: AsyncSession, Model=RiverReading):
        super().__init__(db, Model)

    async def latest_per_station(self) -> list[dict]:
        """Most recent reading of every station (DISTINCT ON)."""
        query = (select(RiverReading.station_code, RiverReading.ts, *VALUE_COLUMNS, *DEVICE_COLUMNS)
                 .distinct(RiverReading.station_code)
                 .order_by(RiverReading.station_code, RiverReading.ts.desc()))
        return await self._rows(query)

    async def latest(self, station_code: str) -> dict | None:
        query = (select(RiverReading.station_code, RiverReading.ts, *VALUE_COLUMNS, *DEVICE_COLUMNS)
                 .where(RiverReading.station_code == station_code).order_by(RiverReading.ts.desc()).limit(1))
        row = (await self.db.execute(query)).mappings().first()
        return dict(row) if row else None

    async def latest_water_level_per_station(self) -> dict[str, float]:
        query = (select(RiverReading.station_code, RiverReading.water_level)
                 .where(RiverReading.water_level.is_not(None))
                 .distinct(RiverReading.station_code)
                 .order_by(RiverReading.station_code, RiverReading.ts.desc()))
        return {r["station_code"]: r["water_level"] for r in await self._rows(query)}

    async def last_ts_per_station(self) -> dict[str, datetime]:
        query = select(RiverReading.station_code, func.max(RiverReading.ts).label("ts")).group_by(RiverReading.station_code)
        return {r["station_code"]: r["ts"] for r in await self._rows(query)}

    async def at_time(self, ts: datetime) -> list[dict]:
        """Reading of every station at (or just before) `ts`."""
        query = (select(RiverReading.station_code, RiverReading.ts, *VALUE_COLUMNS)
                 .where(RiverReading.ts <= ts)
                 .distinct(RiverReading.station_code)
                 .order_by(RiverReading.station_code, RiverReading.ts.desc()))
        return await self._rows(query)

    async def series(self, station_code: str, columns: list[str], start: datetime, end: datetime,
                     bucket_minutes: int) -> list[dict]:
        """Readings between start and end; averaged into buckets when bucket_minutes > 15."""
        cols = [getattr(RiverReading, c) for c in columns]
        if bucket_minutes <= 15:
            query = (select(RiverReading.ts.label("t"), *cols)
                     .where(RiverReading.station_code == station_code, RiverReading.ts.between(start, end))
                     .order_by(RiverReading.ts))
        else:
            bucket = func.date_bin(func.make_interval(0, 0, 0, 0, 0, int(bucket_minutes)), RiverReading.ts,
                                   func.to_timestamp(0)).label("t")
            query = (select(bucket, *[func.round(func.avg(c).cast(Numeric), 3).label(c.key) for c in cols])
                     .where(RiverReading.station_code == station_code, RiverReading.ts.between(start, end))
                     .group_by(bucket).order_by(bucket))
        return await self._rows(query)

    async def hourly_window(self, station_code: str, start: datetime, end: datetime) -> list[dict]:
        """On-the-hour readings in a window (used for alert evaluation)."""
        query = (select(RiverReading.ts, *VALUE_COLUMNS)
                 .where(RiverReading.station_code == station_code, RiverReading.ts.between(start, end),
                        func.extract("minute", RiverReading.ts) == 0)
                 .order_by(RiverReading.ts))
        return await self._rows(query)

    async def monthly_means(self, start: datetime) -> list[dict]:
        """Monthly mean of the River Health Index inputs per station."""
        month = func.date_trunc("month", RiverReading.ts).label("month")
        keys = ("do", "bod", "ammonium", "turbidity", "ph", "ec")
        query = (select(RiverReading.station_code, month, *[func.avg(getattr(RiverReading, k)).label(k) for k in keys])
                 .where(RiverReading.ts >= start)
                 .group_by(RiverReading.station_code, month)
                 .order_by(month, RiverReading.station_code))
        return await self._rows(query)
