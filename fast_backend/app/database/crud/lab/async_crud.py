from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.base.async_base import CrudBase
from app.database.models import Campaign, Compound, Detection, Sample, SourceApportionment, Station


class Lab_crud(CrudBase):

    def __init__(self, db: AsyncSession, Model=Sample):
        super().__init__(db, Model)

    async def get_campaigns(self) -> list[dict]:
        n = (select(func.count()).where(Sample.campaign_code == Campaign.campaign_code).scalar_subquery()).label("samples")
        query = select(Campaign.campaign_code, Campaign.name, Campaign.season, Campaign.start_date, Campaign.end_date,
                       Campaign.campaign_type, Campaign.trigger, n).order_by(Campaign.start_date)
        return await self._rows(query)

    async def campaign_exists(self, campaign_code: str) -> bool:
        return bool(await self.db.scalar(select(func.count()).where(Campaign.campaign_code == campaign_code)))

    async def get_compounds(self) -> list[dict]:
        return await self._rows(select(Compound.name, Compound.compound_class, Compound.marker_for, Compound.pnec_ng_l)
                                .order_by(Compound.name))

    async def get_samples(self, campaign_code: str | None, station_code: str | None) -> list[dict]:
        query = select(Sample.sample_code, Sample.campaign_code, Sample.station_code, Sample.site, Sample.matrix,
                       Sample.lat, Sample.lon, Sample.collected_at, Sample.collector).order_by(Sample.collected_at)
        if campaign_code:
            query = query.where(Sample.campaign_code == campaign_code)
        if station_code:
            query = query.where(Sample.station_code == station_code)
        return await self._rows(query)

    async def get_detections(self, sample_codes: list[str]) -> list[dict]:
        if not sample_codes:
            return []
        query = (select(Detection.sample_code, Detection.compound, Compound.compound_class, Compound.marker_for,
                        Detection.concentration_ng_l, Compound.pnec_ng_l, Detection.screening)
                 .join(Compound, Compound.name == Detection.compound)
                 .where(Detection.sample_code.in_(sample_codes)))
        return await self._rows(query)

    async def get_apportionment(self, campaign_code: str) -> list[dict]:
        query = (select(SourceApportionment.station_code, Station.name.label("site"), SourceApportionment.source,
                        SourceApportionment.share_pct)
                 .join(Station, Station.station_code == SourceApportionment.station_code)
                 .where(SourceApportionment.campaign_code == campaign_code)
                 .order_by(Station.chainage_km, SourceApportionment.id))
        return await self._rows(query)

    async def count_samples(self, campaign_code: str) -> int:
        return await self.db.scalar(select(func.count()).where(Sample.campaign_code == campaign_code))

    async def latest_seasonal_campaign(self) -> str | None:
        return await self.db.scalar(select(Campaign.campaign_code).where(Campaign.campaign_type == "seasonal")
                                    .order_by(Campaign.start_date.desc()).limit(1))
