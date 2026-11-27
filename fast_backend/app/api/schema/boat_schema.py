from typing import Literal

from pydantic import BaseModel


class Waypoint(BaseModel):
    seq: int
    lat: float
    lon: float
    label: str
    action: str                 # sample | measure
    bottle: int | None
    status: str                 # done | active | pending


class Bottle(BaseModel):
    id: int
    volume_ml: int
    filled: bool
    waypoint: int | None
    filled_at: str | None


class BoatStatus(BaseModel):
    vessel: str
    mode: str                   # manual | auto
    state: str                  # idle | navigating | sampling | returning
    lat: float
    lon: float
    heading_deg: float
    speed_mps: float
    battery_pct: float
    signal: str
    gps_fix: str
    last_update: str
    mission_id: str
    mission_name: str
    waypoints: list[Waypoint]
    bottles: list[Bottle]
    track: list[list[float]]    # [[lat, lon], ...]
    water_quality: dict[str, float]


class BoatCommand(BaseModel):
    command: Literal["goto", "sample", "measure", "pause", "resume", "return_home", "set_mode"]
    lat: float | None = None
    lon: float | None = None
    bottle: int | None = None
    mode: Literal["manual", "auto"] | None = None


class CommandAck(BaseModel):
    accepted: bool
    command: str
    queued_at: str
    message: str


class CommandRecord(BaseModel):
    id: int
    command: str
    lat: float | None
    lon: float | None
    bottle: int | None
    mode: str | None
    status: str
    message: str
    queued_at: str
