# LC-HRMS fingerprint analysis of emerging pollutants (SRMS component 2.4).
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    campaign_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    season: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    campaign_type: Mapped[str] = mapped_column(String, nullable=False)       # seasonal | event
    trigger: Mapped[Optional[str]] = mapped_column(String)                   # IoT alert that triggered an event campaign


class Compound(Base):
    __tablename__ = "compounds"

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    compound_class: Mapped[str] = mapped_column(String, nullable=False)
    marker_for: Mapped[str] = mapped_column(String, nullable=False)          # source it fingerprints
    pnec_ng_l: Mapped[float] = mapped_column(Float, nullable=False)          # predicted no-effect concentration


class Sample(Base):
    __tablename__ = "samples"

    sample_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    campaign_code: Mapped[str] = mapped_column(ForeignKey("campaigns.campaign_code", ondelete="CASCADE"), nullable=False, index=True)
    station_code: Mapped[str] = mapped_column(ForeignKey("stations.station_code", ondelete="CASCADE"), nullable=False, index=True)
    site: Mapped[str] = mapped_column(String, nullable=False)
    matrix: Mapped[str] = mapped_column(String, nullable=False)              # water | sediment | groundwater
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    collector: Mapped[str] = mapped_column(String, nullable=False)           # autosampler | boat | manual


class Detection(Base):
    __tablename__ = "detections"
    __table_args__ = (UniqueConstraint("sample_code", "compound", name="uq_detections_sample_compound"),)

    sample_code: Mapped[str] = mapped_column(ForeignKey("samples.sample_code", ondelete="CASCADE"), nullable=False, index=True)
    compound: Mapped[str] = mapped_column(ForeignKey("compounds.name", ondelete="CASCADE"), nullable=False)
    concentration_ng_l: Mapped[float] = mapped_column(Float, nullable=False)
    screening: Mapped[str] = mapped_column(String, nullable=False)           # target | suspect | non-target


class SourceApportionment(Base):
    """Share of pollutant load by source at a site for one campaign (PMF / fingerprint model output)."""
    __tablename__ = "source_apportionment"
    __table_args__ = (UniqueConstraint("campaign_code", "station_code", "source", name="uq_source_apportionment"),)

    campaign_code: Mapped[str] = mapped_column(ForeignKey("campaigns.campaign_code", ondelete="CASCADE"), nullable=False, index=True)
    station_code: Mapped[str] = mapped_column(ForeignKey("stations.station_code", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    share_pct: Mapped[float] = mapped_column(Float, nullable=False)
