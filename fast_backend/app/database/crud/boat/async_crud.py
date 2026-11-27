from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.base.async_base import CrudBase
from app.database.models import BoatCommand, BoatMission, BoatWaypoint


class Boat_crud(CrudBase):

    def __init__(self, db: AsyncSession, Model=BoatMission):
        super().__init__(db, Model)

    async def active_mission(self) -> dict | None:
        query = (select(BoatMission.mission_code, BoatMission.name, BoatMission.vessel, BoatMission.loop_minutes)
                 .where(BoatMission.is_active.is_(True)).order_by(BoatMission.id.desc()).limit(1))
        row = (await self.db.execute(query)).mappings().first()
        return dict(row) if row else None

    async def waypoints(self, mission_code: str) -> list[dict]:
        query = (select(BoatWaypoint.seq, BoatWaypoint.lat, BoatWaypoint.lon, BoatWaypoint.label, BoatWaypoint.action,
                        BoatWaypoint.bottle)
                 .where(BoatWaypoint.mission_code == mission_code).order_by(BoatWaypoint.seq))
        return await self._rows(query)

    async def add_command(self, data: dict) -> dict:
        cmd = BoatCommand(**data)
        self.db.add(cmd)
        await self.db.flush()
        await self.db.refresh(cmd)
        return {"id": cmd.id, "command": cmd.command, "status": cmd.status, "message": cmd.message,
                "queued_at": cmd.created_at}

    async def recent_commands(self, limit: int = 50) -> list[dict]:
        query = (select(BoatCommand.id, BoatCommand.command, BoatCommand.lat, BoatCommand.lon, BoatCommand.bottle,
                        BoatCommand.mode, BoatCommand.status, BoatCommand.message, BoatCommand.created_at.label("queued_at"))
                 .order_by(BoatCommand.id.desc()).limit(limit))
        return await self._rows(query)
