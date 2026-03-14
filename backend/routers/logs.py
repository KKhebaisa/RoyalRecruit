"""
Logs router.
Records and retrieves audit log events.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from models import Server, AuditLog
from auth.security import get_current_user_id, require_bot_api_key

logger = logging.getLogger(__name__)
router = APIRouter()


class LogCreate(BaseModel):
    server_discord_id:    str
    event_type:           str
    actor_discord_id:     Optional[str] = None
    target_discord_id:    Optional[str] = None
    details:              Optional[dict] = None


@router.post("/", dependencies=[Depends(require_bot_api_key)])
async def create_log(
    payload: LogCreate,
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(Server).where(Server.discord_server_id == payload.server_discord_id)
    )
    server = r.scalar_one_or_none()
    if not server:
        raise HTTPException(404, "Server not found")

    log = AuditLog(
        server_id        = server.id,
        event_type       = payload.event_type,
        actor_discord_id = payload.actor_discord_id,
        target_discord_id= payload.target_discord_id,
        details          = payload.details,
    )
    db.add(log)
    await db.flush()
    return {"id": log.id}


@router.get("/{server_id}")
async def get_logs(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
    limit: int = 100,
):
    r = await db.execute(
        select(Server).where(Server.discord_server_id == server_id)
    )
    server = r.scalar_one_or_none()
    if not server:
        raise HTTPException(404, "Server not found")

    r = await db.execute(
        select(AuditLog)
        .where(AuditLog.server_id == server.id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    logs = r.scalars().all()
    return [
        {
            "id":               l.id,
            "event_type":       l.event_type,
            "actor_discord_id": l.actor_discord_id,
            "details":          l.details,
            "created_at":       l.created_at.isoformat(),
        }
        for l in logs
    ]
