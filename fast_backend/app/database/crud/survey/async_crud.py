from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.base.async_base import CrudBase
from app.database.models import CrossSection, Hotspot, Survey, TemTransect

TRANSECT_COLUMNS = [
    TemTransect.transect_code, TemTransect.name, TemTransect.survey_date, TemTransect.length_m, TemTransect.start_lat,
    TemTransect.start_lon, TemTransect.end_lat, TemTransect.end_lon, TemTransect.station_code, TemTransect.finding,
]


class Survey_crud(CrudBase):

    def __init__(self, db: AsyncSession, Model=Survey):
        super().__init__(db, Model)

    # ---- TEM ----
    async def get_transects(self) -> list[dict]:
        return await self._rows(select(*TRANSECT_COLUMNS).order_by(TemTransect.transect_code))

    async def get_section(self, transect_code: str) -> dict | None:
        query = select(TemTransect.transect_code, TemTransect.distances_m, TemTransect.depths_m, TemTransect.resistivity,
                       TemTransect.interpretation).where(TemTransect.transect_code == transect_code)
        row = (await self.db.execute(query)).mappings().first()
        return dict(row) if row else None

    # ---- drone / boat surveys ----
    async def get_surveys(self) -> list[dict]:
        return await self._rows(select(Survey.survey_code, Survey.name, Survey.survey_date, Survey.season, Survey.platform,
                                       Survey.area_km2, Survey.gsd_cm).order_by(Survey.survey_date))

    async def get_hotspots(self, survey_code: str | None, hotspot_type: str | None) -> list[dict]:
        query = select(Hotspot.hotspot_code, Hotspot.hotspot_type, Hotspot.lat, Hotspot.lon, Hotspot.survey_code,
                       Hotspot.detail, Hotspot.severity).order_by(Hotspot.hotspot_code)
        if survey_code:
            query = query.where(Hotspot.survey_code == survey_code)
        if hotspot_type:
            query = query.where(func.lower(Hotspot.hotspot_type) == hotspot_type.lower())
        return await self._rows(query)

    async def count_hotspots(self) -> int:
        return await self.db.scalar(select(func.count()).select_from(Hotspot))

    async def get_cross_sections(self) -> list[dict]:
        return await self._rows(select(CrossSection.chainage_km, CrossSection.location, CrossSection.offsets_m,
                                       CrossSection.pre_monsoon_bed_m, CrossSection.post_monsoon_bed_m,
                                       CrossSection.net_change_m2).order_by(CrossSection.chainage_km))
