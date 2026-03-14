"""
Guilds router – manage server records and settings.
Dashboard settings endpoint requires guild ADMINISTRATOR permission.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from models import Server
from auth.security import get_current_user_id, require_bot_api_key, make_guild_admin_dep

logger = logging.getLogger(__name__)
router = APIRouter()


class ServerUpsert(BaseModel):
    discord_server_id: str = Field(..., max_length=32)
    name:              str = Field(..., min_length=1, max_length=200)
    icon:              Optional[str] = Field(None, max_length=256)
    owner_discord_id:  str = Field(..., max_length=32)


class ServerSettings(BaseModel):
    log_channel_id: Optional[str] = Field(None, max_length=32)


async def _get_server_or_404(server_id: str, db: AsyncSession) -> Server:
    result = await db.execute(
        select(Server).where(Server.discord_server_id == server_id)
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@router.get("/{server_id}")
async def get_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),    # ← guild admin guard
):
    server = await _get_server_or_404(server_id, db)
    return {
        "id":                server.id,
        "discord_server_id": server.discord_server_id,
        "name":              server.name,
        "icon":              server.icon,
        "log_channel_id":    server.log_channel_id,
    }


@router.post("/upsert", dependencies=[Depends(require_bot_api_key)])
async def upsert_server(
    payload: ServerUpsert,
    db: AsyncSession = Depends(get_db),
):
    """Bot calls this when it joins or updates a guild."""
    result = await db.execute(
        select(Server).where(Server.discord_server_id == payload.discord_server_id)
    )
    server = result.scalar_one_or_none()

    if server:
        server.name             = payload.name
        server.icon             = payload.icon
        server.owner_discord_id = payload.owner_discord_id
    else:
        server = Server(
            discord_server_id= payload.discord_server_id,
            name             = payload.name,
            icon             = payload.icon,
            owner_discord_id = payload.owner_discord_id,
        )
        db.add(server)

    await db.flush()
    return {"id": server.id, "discord_server_id": server.discord_server_id}


@router.patch("/{server_id}/settings")
async def update_settings(
    server_id: str,
    payload: ServerSettings,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),    # ← guild admin guard
):
    server = await _get_server_or_404(server_id, db)
    if payload.log_channel_id is not None:
        server.log_channel_id = payload.log_channel_id
    return {"ok": True}
