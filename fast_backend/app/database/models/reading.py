# Time series pushed by the IoT stations (15-min interval). One row per station per timestamp.
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base

# Parameter columns of river_readings; keys match parameters.key.
READING_COLUMNS = (
    "ph", "do", "ec", "turbidity", "temperature", "orp", "nitrate", "ammonium", "phosphate", "chlorophyll",
    "bod", "cod", "water_level", "flow", "rainfall", "air_temp", "humidity",
)


class RiverReading(Base):
    __tablename__ = "river_readings"
    __table_args__ = (
        UniqueConstraint("station_code", "ts", name="uq_river_readings_station_ts"),
        Index("ix_river_readings_station_ts", "station_code", "ts"),
    )

    station_code: Mapped[str] = mapped_column(ForeignKey("stations.station_code", ondelete="CASCADE"), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="device")   # device | simulator

    # water quality
    ph: Mapped[Optional[float]] = mapped_column(Float)
    do: Mapped[Optional[float]] = mapped_column(Float)
    ec: Mapped[Optional[float]] = mapped_column(Float)
    turbidity: Mapped[Optional[float]] = mapped_column(Float)
    temperature: Mapped[Optional[float]] = mapped_column(Float)
    orp: Mapped[Optional[float]] = mapped_column(Float)
    # nutrients
    nitrate: Mapped[Optional[float]] = mapped_column(Float)
    ammonium: Mapped[Optional[float]] = mapped_column(Float)
    phosphate: Mapped[Optional[float]] = mapped_column(Float)
    chlorophyll: Mapped[Optional[float]] = mapped_column(Float)
    # organic load (sensor proxies)
    bod: Mapped[Optional[float]] = mapped_column(Float)
    cod: Mapped[Optional[float]] = mapped_column(Float)
    # hydrology
    water_level: Mapped[Optional[float]] = mapped_column(Float)
    flow: Mapped[Optional[float]] = mapped_column(Float)
    # meteorology
    rainfall: Mapped[Optional[float]] = mapped_column(Float)
    air_temp: Mapped[Optional[float]] = mapped_column(Float)
    humidity: Mapped[Optional[float]] = mapped_column(Float)
    # device health
    battery_v: Mapped[Optional[float]] = mapped_column(Float)
    signal_dbm: Mapped[Optional[float]] = mapped_column(Float)
