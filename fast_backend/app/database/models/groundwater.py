# Groundwater loggers sited from TEM results (SRMS 2.1 -> 2.2).
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


class Well(Base):
    __tablename__ = "wells"

    well_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    paired_station: Mapped[str] = mapped_column(ForeignKey("stations.station_code", ondelete="CASCADE"), nullable=False)
    depth_m: Mapped[float] = mapped_column(Float, nullable=False)
    zone: Mapped[str] = mapped_column(String, nullable=False)      # TEM interpretation of the site


class WellReading(Base):
    __tablename__ = "well_readings"
    __table_args__ = (
        UniqueConstraint("well_code", "ts", name="uq_well_readings_well_ts"),
        Index("ix_well_readings_well_ts", "well_code", "ts"),
    )

    well_code: Mapped[str] = mapped_column(ForeignKey("wells.well_code", ondelete="CASCADE"), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    depth_to_water_m: Mapped[float] = mapped_column(Float, nullable=False)
    ec: Mapped[float] = mapped_column(Float, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
