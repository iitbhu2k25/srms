from fastapi import APIRouter

from app.api.schema.lab_schema import Campaign, Compound, Sample, SourceApportionment
from app.api.service.lab_svc import lab_svc
from app.database.config.dependency import db_read

router = APIRouter()


@router.get("/campaigns", response_model=list[Campaign])
async def get_campaigns(db: db_read):
    return await lab_svc.get_campaigns(db)


@router.get("/compounds", response_model=list[Compound])
async def get_compounds(db: db_read):
    return await lab_svc.get_compounds(db)


@router.get("/samples", response_model=list[Sample])
async def get_samples(db: db_read, campaign_id: str | None = None, station_id: str | None = None):
    return await lab_svc.get_samples(db, campaign_id, station_id)


@router.get("/apportionment/{campaign_code}", response_model=list[SourceApportionment])
async def get_apportionment(db: db_read, campaign_code: str):
    return await lab_svc.get_apportionment(db, campaign_code)
