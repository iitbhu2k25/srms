# GIS layers of the Varuna basin (WGS84), loaded from the shapefiles in media/ (Boundary, Rivers, Drains, STP).
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import Float, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


class BasinBoundary(Base):
    """Varuna basin outline (media/Boundary)."""
    __tablename__ = "basin_boundary"

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    geom = mapped_column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=True), nullable=False)


class River(Base):
    """Main stem and tributaries (media/Rivers): Varuna, Morwa, Basuhi."""
    __tablename__ = "rivers"

    river_code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    length_km: Mapped[float] = mapped_column(Float, nullable=False)
    geom = mapped_column(Geometry("MULTILINESTRING", srid=4326, spatial_index=True), nullable=False)


class Drain(Base):
    """Drain outfalls (media/Drains). Missing values (-999 in the source) are stored as NULL."""
    __tablename__ = "drains"

    drain_code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String)                     # NULL when "Unknown" in the source
    river_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    river_code: Mapped[int] = mapped_column(Integer, nullable=False)
    tapping_status: Mapped[str] = mapped_column(String, nullable=False)     # Tapped | Untapped | Partial
    discharge: Mapped[Optional[float]] = mapped_column(Float)               # as surveyed (MLD)
    elevation_m: Mapped[Optional[float]] = mapped_column(Float)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    geom = mapped_column(Geometry("POINT", srid=4326, spatial_index=True), nullable=False)


class Stp(Base):
    """Sewage treatment plants (media/STP): footprint polygon, compliance and actual vs design effluent quality."""
    __tablename__ = "stps"

    stp_code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String)                   # Compliant | Non-compliant | ...
    maintained_by: Mapped[Optional[str]] = mapped_column(String)
    stp_type: Mapped[Optional[str]] = mapped_column(String)                 # Existing | Proposed | ...
    capacity_mld: Mapped[Optional[float]] = mapped_column(Float)
    utilized_mld: Mapped[Optional[float]] = mapped_column(Float)
    bod_actual: Mapped[Optional[float]] = mapped_column(Float)
    bod_design: Mapped[Optional[float]] = mapped_column(Float)
    cod_actual: Mapped[Optional[float]] = mapped_column(Float)
    cod_design: Mapped[Optional[float]] = mapped_column(Float)
    tss_actual: Mapped[Optional[float]] = mapped_column(Float)
    tss_design: Mapped[Optional[float]] = mapped_column(Float)
    ph_actual: Mapped[Optional[float]] = mapped_column(Float)
    ph_design: Mapped[Optional[float]] = mapped_column(Float)
    fc_actual: Mapped[Optional[float]] = mapped_column(Float)
    fc_design: Mapped[Optional[float]] = mapped_column(Float)
    remarks: Mapped[Optional[str]] = mapped_column(String)
    tapped_drains: Mapped[Optional[list[int]]] = mapped_column(ARRAY(Integer))  # drain codes
    river_name: Mapped[Optional[str]] = mapped_column(String)
    district: Mapped[Optional[str]] = mapped_column(String)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    geom = mapped_column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=True), nullable=False)
