"""
Panels router.
Manages panel configurations (embeds + buttons sent to Discord channels).
All dashboard-facing endpoints require the caller to be a guild ADMINISTRATOR.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.connection import get_db
from models import Server, Panel, PanelType, TicketType, ApplicationType
from auth.security import get_current_user_id, require_bot_api_key, make_guild_admin_dep

logger = logging.getLogger(__name__)
router = APIRouter()


class PanelCreate(BaseModel):
    panel_type:           PanelType
    title:                str = Field(..., min_length=1, max_length=256)
    description:          Optional[str] = Field(None, max_length=4096)
    color:                Optional[int] = Field(0x5865F2, ge=0, le=0xFFFFFF)
    channel_id:           Optional[str] = Field(None, max_length=32)
    ticket_type_ids:      List[int] = Field(default_factory=list, max_items=25)
    application_type_ids: List[int] = Field(default_factory=list, max_items=25)


class PanelMessageIdUpdate(BaseModel):
    message_id: str = Field(..., max_length=32)


async def _get_server(server_id: str, db: AsyncSession) -> Server:
    r = await db.execute(select(Server).where(Server.discord_server_id == server_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Server not found")
    return s


def _panel_to_dict(p: Panel) -> dict:
    return {
        "id":          p.id,
        "panel_type":  p.panel_type,
        "title":       p.title,
        "description": p.description,
        "color":       p.color,
        "channel_id":  p.channel_id,
        "message_id":  p.message_id,
        "ticket_types": [
            {"id": t.id, "ticket_name": t.ticket_name, "button_label": t.button_label}
            for t in p.ticket_types
        ],
        "application_types": [
            {"id": a.id, "application_name": a.application_name, "button_label": a.button_label}
            for a in p.application_types
        ],
    }


@router.get("/{server_id}")
async def list_panels(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),   # ← guild admin guard
):
    server = await _get_server(server_id, db)
    r = await db.execute(
        select(Panel)
        .where(Panel.server_id == server.id)
        .options(
            selectinload(Panel.ticket_types),
            selectinload(Panel.application_types),
        )
    )
    panels = r.scalars().all()
    return [_panel_to_dict(p) for p in panels]


@router.post("/{server_id}")
async def create_panel(
    server_id: str,
    payload: PanelCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),   # ← guild admin guard
):
    server = await _get_server(server_id, db)
    panel = Panel(
        server_id   = server.id,
        panel_type  = payload.panel_type,
        title       = payload.title,
        description = payload.description,
        color       = payload.color,
        channel_id  = payload.channel_id,
    )

    # Validate that the ticket/app types belong to this server before attaching
    if payload.ticket_type_ids:
        r = await db.execute(
            select(TicketType).where(
                TicketType.id.in_(payload.ticket_type_ids),
                TicketType.server_id == server.id,     # ← prevents cross-server injection
            )
        )
        panel.ticket_types = r.scalars().all()

    if payload.application_type_ids:
        r = await db.execute(
            select(ApplicationType).where(
                ApplicationType.id.in_(payload.application_type_ids),
                ApplicationType.server_id == server.id,  # ← prevents cross-server injection
            )
        )
        panel.application_types = r.scalars().all()

    db.add(panel)
    await db.flush()
    return {"id": panel.id}


@router.delete("/{server_id}/{panel_id}")
async def delete_panel(
    server_id: str,
    panel_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),   # ← guild admin guard
):
    server = await _get_server(server_id, db)
    r = await db.execute(
        select(Panel).where(Panel.id == panel_id, Panel.server_id == server.id)
    )
    panel = r.scalar_one_or_none()
    if not panel:
        raise HTTPException(404, "Panel not found")
    await db.delete(panel)
    return {"ok": True}


@router.patch("/{panel_id}/message_id", dependencies=[Depends(require_bot_api_key)])
async def update_panel_message_id(
    panel_id: int,
    payload: PanelMessageIdUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Bot calls this after sending the panel embed to record the Discord message ID."""
    r = await db.execute(select(Panel).where(Panel.id == panel_id))
    panel = r.scalar_one_or_none()
    if not panel:
        raise HTTPException(404, "Panel not found")
    panel.message_id = payload.message_id
    return {"ok": True}


@router.get("/bot/{server_id}", dependencies=[Depends(require_bot_api_key)])
async def bot_get_panels(
    server_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Bot fetches all panels for a guild."""
    server = await _get_server(server_id, db)
    r = await db.execute(
        select(Panel)
        .where(Panel.server_id == server.id)
        .options(
            selectinload(Panel.ticket_types),
            selectinload(Panel.application_types),
        )
    )
    panels = r.scalars().all()
    return [_panel_to_dict(p) for p in panels]
