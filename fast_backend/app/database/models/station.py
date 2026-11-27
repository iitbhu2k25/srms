# IoT river monitoring network (SRMS component 2.2): stations and the parameter dictionary.
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


class Station(Base):
    __tablename__ = "stations"

    station_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)   # e.g. VR-05
    name: Mapped[str] = mapped_column(String, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    reach: Mapped[str] = mapped_column(String, nullable=False)
    district: Mapped[str] = mapped_column(String, nullable=False)
    chainage_km: Mapped[float] = mapped_column(Float, nullable=False)                # distance from origin
    telemetry: Mapped[str] = mapped_column(String, nullable=False)                  # GSM | LoRaWAN | NB-IoT
    installed: Mapped[date] = mapped_column(Date, nullable=False)
    device_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)     # id the device sends on ingest
    # Dummy-simulator profile (clean | moderate | poor | severe); unused for real devices.
    profile: Mapped[str] = mapped_column(String, nullable=False, default="moderate")
    # Inactive stations are not fed by the simulator (demonstrates the "offline" state).
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Parameter(Base):
    """Measured parameter: label, unit and permissible limits (CPCB Class-B used as a guide)."""
    __tablename__ = "parameters"

    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)           # column name in river_readings
    label: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False, default="")
    min_limit: Mapped[Optional[float]] = mapped_column(Float)
    max_limit: Mapped[Optional[float]] = mapped_column(Float)
    group_name: Mapped[str] = mapped_column(String, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
