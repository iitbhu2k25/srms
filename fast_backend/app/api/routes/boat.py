from fastapi import APIRouter

from app.api.schema.boat_schema import BoatCommand, BoatStatus, CommandAck, CommandRecord
from app.api.service.boat_svc.boat import boat_svc
from app.database.config.dependency import db_read, db_write

router = APIRouter()


@router.get("/status", response_model=BoatStatus)
async def get_status(db: db_read):
    """Live position, mission progress, sample bottles and on-board water quality."""
    return await boat_svc.get_status(db)


@router.post("/command", response_model=CommandAck)
async def add_command(db: db_write, cmd: BoatCommand):
    """Queue a navigation / sampling command (stored; no vessel connected yet)."""
    return await boat_svc.add_command(db, cmd.model_dump())


@router.get("/commands", response_model=list[CommandRecord])
async def get_commands(db: db_read):
    return await boat_svc.get_commands(db)
