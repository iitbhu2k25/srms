from fastapi import APIRouter, Query

from app.api.schema.gis_schema import DrainRecord, DrainSummary, FeatureCollection, GeoFeature, StpRecord
from app.api.service.gis_svc import gis_svc
from app.database.config.dependency import db_read

router = APIRouter()


@router.get("/boundary", response_model=GeoFeature)
async def get_boundary(db: db_read):
    """Varuna basin outline (GeoJSON, simplified)."""
    return await gis_svc.get_boundary(db)


@router.get("/rivers", response_model=FeatureCollection)
async def get_rivers(db: db_read):
    """Varuna, Morwa and Basuhi (GeoJSON, simplified)."""
    return await gis_svc.get_rivers(db)


@router.get("/drains", response_model=list[DrainRecord])
async def get_drains(db: db_read,
                     river: str | None = Query(None, description="e.g. Varuna, Basuhi, Morwa, Ganga"),
                     tapping: str | None = Query(None, description="Tapped | Untapped | Partial")):
    """Drain outfalls (media/Drains)."""
    return await gis_svc.get_drains(db, river, tapping)


@router.get("/drains/summary", response_model=list[DrainSummary])
async def get_drain_summary(db: db_read):
    """Drains per river: tapping status and surveyed discharge (MLD)."""
    return await gis_svc.get_drain_summary(db)


@router.get("/stps", response_model=list[StpRecord])
async def get_stps(db: db_read):
    """Sewage treatment plants: capacity, utilisation and effluent quality (actual vs design)."""
    return await gis_svc.get_stps(db)
