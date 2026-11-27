from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.base.async_base import CrudBase
from app.database.models import Parameter, Station

STATION_COLUMNS = [
    Station.station_code, Station.name, Station.lat, Station.lon, Station.reach, Station.district,
    Station.chainage_km, Station.telemetry, Station.installed, Station.device_id, Station.profile, Station.is_active,
]


class Station_crud(CrudBase):

    def __init__(self, db: AsyncSession, Model=Station):
        super().__init__(db, Model)

    async def get_stations(self) -> list[dict]:
        return await self._rows(select(*STATION_COLUMNS).order_by(Station.chainage_km))

    async def get_station(self, station_code: str) -> dict | None:
        row = (await self.db.execute(select(*STATION_COLUMNS).where(Station.station_code == station_code))).mappings().first()
        return dict(row) if row else None

    async def get_by_device(self, device_id: str) -> dict | None:
        row = (await self.db.execute(select(*STATION_COLUMNS).where(Station.device_id == device_id))).mappings().first()
        return dict(row) if row else None

    async def get_parameters(self) -> list[dict]:
        query = select(Parameter.key, Parameter.label, Parameter.unit, Parameter.min_limit, Parameter.max_limit,
                       Parameter.group_name).order_by(Parameter.sort_order)
        return await self._rows(query)
