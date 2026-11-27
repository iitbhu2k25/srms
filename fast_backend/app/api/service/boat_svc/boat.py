"""
SMART-STREAM boat: status from the active mission (simulated position) and the command log in the database.
In production the position/telemetry come from the boat and commands are forwarded to the on-board Raspberry Pi.
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.service.boat_svc.navigation import haversine, simulate
from app.api.service.simulator_svc.generator import rng
from app.database.crud.boat.async_crud import Boat_crud
from app.database.crud.reading.async_crud import Reading_crud
from app.database.crud.spatial.async_crud import Spatial_crud
from app.database.crud.station.async_crud import Station_crud

WQ_KEYS = ("ph", "do", "ec", "turbidity", "temperature", "orp")


def _iso_utc(dt: datetime) -> str:
    """created_at is stored naive (UTC, server now()); mark it as UTC for the browser."""
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).isoformat()


class boat_svc:

    async def get_status(db: AsyncSession) -> dict:
        crud = Boat_crud(db)
        mission = await crud.active_mission()
        if not mission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active boat mission")
        waypoints = await crud.waypoints(mission["mission_code"])
        now = datetime.now(timezone.utc)
        # The boat follows the river channel (media/Rivers) between the first and last waypoint.
        path = await Spatial_crud(db).river_path("Varuna", (waypoints[0]["lat"], waypoints[0]["lon"]),
                                                 (waypoints[-1]["lat"], waypoints[-1]["lon"]))
        sim = simulate(waypoints, mission["loop_minutes"], now, path)

        # On-board water quality: latest reading of the nearest IoT station (stand-in for the ESP32 unit).
        stations = await Station_crud(db).get_stations()
        nearest = min(stations, key=lambda s: haversine((sim["lat"], sim["lon"]), (s["lat"], s["lon"])))
        wq = await Reading_crud(db).latest(nearest["station_code"]) or {}
        r = rng("boat", now.replace(second=0, microsecond=0))

        return {
            "vessel": mission["vessel"], "mode": "auto", "state": sim["state"],
            "lat": round(sim["lat"], 6), "lon": round(sim["lon"], 6), "heading_deg": sim["heading_deg"],
            "speed_mps": 0.0 if sim["state"] == "sampling" else round(1.1 + r.random() * 0.4, 2),
            "battery_pct": round(100 - sim["progress"] * 38, 1),
            "signal": "4G · -71 dBm", "gps_fix": "RTK float · 0.4 m", "last_update": now.isoformat(),
            "mission_id": mission["mission_code"], "mission_name": mission["name"],
            "waypoints": sim["waypoints"], "bottles": sim["bottles"], "track": sim["track"], "route": sim["route"],
            "water_quality": {k: wq[k] for k in WQ_KEYS if wq.get(k) is not None},
        }

    async def add_command(db: AsyncSession, cmd: dict) -> dict:
        desc = cmd["command"].replace("_", " ")
        if cmd["command"] == "goto":
            desc += f" → {cmd.get('lat')}, {cmd.get('lon')}"
        if cmd["command"] == "sample" and cmd.get("bottle"):
            desc += f" into bottle {cmd['bottle']}"
        message = f"Command queued: {desc} (simulation — no vessel connected)"
        row = await Boat_crud(db).add_command({**cmd, "status": "queued", "message": message})
        return {"accepted": True, "command": row["command"], "queued_at": _iso_utc(row["queued_at"]), "message": message}

    async def get_commands(db: AsyncSession) -> list[dict]:
        return [{**c, "queued_at": _iso_utc(c["queued_at"])} for c in await Boat_crud(db).recent_commands()]
