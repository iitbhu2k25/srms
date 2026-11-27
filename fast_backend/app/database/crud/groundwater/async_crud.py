from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.base.async_base import CrudBase
from app.database.models import RiverReading, Well, WellReading

WELL_COLUMNS = [Well.well_code, Well.name, Well.lat, Well.lon, Well.paired_station, Well.depth_m, Well.zone]


class Groundwater_crud(CrudBase):

    def __init__(self, db: AsyncSession, Model=Well):
        super().__init__(db, Model)

    async def get_wells(self) -> list[dict]:
        return await self._rows(select(*WELL_COLUMNS).order_by(Well.well_code))

    async def get_well(self, well_code: str) -> dict | None:
        row = (await self.db.execute(select(*WELL_COLUMNS).where(Well.well_code == well_code))).mappings().first()
        return dict(row) if row else None

    async def latest_per_well(self) -> dict[str, dict]:
        query = (select(WellReading.well_code, WellReading.ts, WellReading.depth_to_water_m, WellReading.ec,
                        WellReading.temperature)
                 .distinct(WellReading.well_code).order_by(WellReading.well_code, WellReading.ts.desc()))
        return {r["well_code"]: r for r in await self._rows(query)}

    async def last_ts_per_well(self) -> dict[str, datetime]:
        query = select(WellReading.well_code, func.max(WellReading.ts).label("ts")).group_by(WellReading.well_code)
        return {r["well_code"]: r["ts"] for r in await self._rows(query)}

    async def series_with_river(self, well: dict, start: datetime, bucket_hours: int) -> list[dict]:
        """Well readings averaged into buckets, joined with the paired station's mean river level per bucket."""
        def bucket(col):
            return func.date_bin(func.make_interval(0, 0, 0, 0, bucket_hours), col, func.to_timestamp(0)).label("t")

        wb = bucket(WellReading.ts)
        well_q = (select(wb, func.avg(WellReading.depth_to_water_m).label("depth_to_water_m"),
                         func.avg(WellReading.ec).label("ec"), func.avg(WellReading.temperature).label("temperature"))
                  .where(WellReading.well_code == well["well_code"], WellReading.ts >= start)
                  .group_by(wb).subquery())
        rb = bucket(RiverReading.ts)
        river_q = (select(rb, func.avg(RiverReading.water_level).label("river_level_m"))
                   .where(RiverReading.station_code == well["paired_station"], RiverReading.ts >= start)
                   .group_by(rb).subquery())
        query = (select(well_q.c.t, well_q.c.depth_to_water_m, well_q.c.ec, well_q.c.temperature, river_q.c.river_level_m)
                 .join(river_q, river_q.c.t == well_q.c.t, isouter=True).order_by(well_q.c.t))
        return await self._rows(query)
