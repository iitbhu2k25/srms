# TEM geophysics (SRMS 2.1) and drone / autonomous-boat surveys (SRMS 2.3).
from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


class TemTransect(Base):
    __tablename__ = "tem_transects"

    transect_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    survey_date: Mapped[date] = mapped_column(Date, nullable=False)
    length_m: Mapped[float] = mapped_column(Float, nullable=False)
    start_lat: Mapped[float] = mapped_column(Float, nullable=False)
    start_lon: Mapped[float] = mapped_column(Float, nullable=False)
    end_lat: Mapped[float] = mapped_column(Float, nullable=False)
    end_lon: Mapped[float] = mapped_column(Float, nullable=False)
    station_code: Mapped[Optional[str]] = mapped_column(ForeignKey("stations.station_code", ondelete="SET NULL"))
    finding: Mapped[str] = mapped_column(String, nullable=False)
    # 2-D resistivity section from stitched 1-D inversions
    distances_m: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    depths_m: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    resistivity: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)     # [depth][distance] ohm-m
    interpretation: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


class Survey(Base):
    __tablename__ = "surveys"

    survey_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    survey_date: Mapped[date] = mapped_column(Date, nullable=False)
    season: Mapped[str] = mapped_column(String, nullable=False)
    platform: Mapped[str] = mapped_column(String, nullable=False)
    area_km2: Mapped[float] = mapped_column(Float, nullable=False)
    gsd_cm: Mapped[float] = mapped_column(Float, nullable=False)


class Hotspot(Base):
    __tablename__ = "hotspots"

    hotspot_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hotspot_type: Mapped[str] = mapped_column(String, nullable=False)    # Outfall | Encroachment | Siltation | ...
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    survey_code: Mapped[str] = mapped_column(ForeignKey("surveys.survey_code", ondelete="CASCADE"), nullable=False, index=True)
    detail: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)        # high | medium | low


class CrossSection(Base):
    """Bathymetric cross-section, pre- vs post-monsoon (echo sounder on the autonomous boat)."""
    __tablename__ = "cross_sections"

    station_code: Mapped[str] = mapped_column(ForeignKey("stations.station_code", ondelete="CASCADE"), unique=True, nullable=False)
    chainage_km: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    offsets_m: Mapped[list] = mapped_column(JSONB, nullable=False)
    pre_monsoon_bed_m: Mapped[list] = mapped_column(JSONB, nullable=False)
    post_monsoon_bed_m: Mapped[list] = mapped_column(JSONB, nullable=False)
    net_change_m2: Mapped[float] = mapped_column(Float, nullable=False)
