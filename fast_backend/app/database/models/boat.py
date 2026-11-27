# SMART-STREAM autonomous boat (Annex XII Part B): missions, waypoints and the command log.
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


class BoatMission(Base):
    __tablename__ = "boat_missions"

    mission_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    vessel: Mapped[str] = mapped_column(String, nullable=False)
    loop_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)  # simulator: one run per loop
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BoatWaypoint(Base):
    __tablename__ = "boat_waypoints"
    __table_args__ = (UniqueConstraint("mission_code", "seq", name="uq_boat_waypoints_mission_seq"),)

    mission_code: Mapped[str] = mapped_column(ForeignKey("boat_missions.mission_code", ondelete="CASCADE"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)          # sample | measure
    bottle: Mapped[Optional[int]] = mapped_column(Integer)


class BoatCommand(Base):
    """Commands issued from the web control (forwarded to the on-board Raspberry Pi in production)."""
    __tablename__ = "boat_commands"

    command: Mapped[str] = mapped_column(String, nullable=False)
    lat: Mapped[Optional[float]] = mapped_column(Float)
    lon: Mapped[Optional[float]] = mapped_column(Float)
    bottle: Mapped[Optional[int]] = mapped_column(Integer)
    mode: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="queued")   # queued | sent | done | failed
    message: Mapped[str] = mapped_column(String, nullable=False, default="")
