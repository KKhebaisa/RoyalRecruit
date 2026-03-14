"""
Tickets router.
Manages TicketType configurations and Ticket instances.
All dashboard-facing endpoints require the caller to be a guild ADMINISTRATOR.
"""

import logging
import re
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.connection import get_db
from models import Server, Ticket, TicketType, TicketCounter, TicketStatus, User
from auth.security import get_current_user_id, require_bot_api_key, make_guild_admin_dep

logger = logging.getLogger(__name__)
router = APIRouter()


def _safe_channel_name(text: str) -> str:
    """Sanitize text for use in a Discord channel name (lowercase, hyphens only, max 32 chars)."""
    return re.sub(r"[^a-z0-9-]", "", text.lower().replace(" ", "-"))[:32]


# ── Schemas ───────────────────────────────────────────────────────────────────

class TicketTypeCreate(BaseModel):
    ticket_name:        str = Field(..., min_length=1, max_length=100)
    ticket_description: Optional[str] = Field(None, max_length=1000)
    ticket_category_id: Optional[str] = Field(None, max_length=32)
    staff_role_id:      Optional[str] = Field(None, max_length=32)
    panel_message:      Optional[str] = Field(None, max_length=2000)
    button_label:       Optional[str] = Field(None, max_length=80)
    button_emoji:       Optional[str] = Field(None, max_length=50)

    @validator("ticket_name")
    def name_no_special(cls, v):
        if not re.match(r"^[\w\s\-]+$", v):
            raise ValueError("Ticket name may only contain letters, numbers, spaces, and hyphens.")
        return v


class TicketCreate(BaseModel):
    """Used by bot to register a newly created ticket."""
    server_discord_id: str = Field(..., max_length=32)
    ticket_type_id:    int
    user_discord_id:   str = Field(..., max_length=32)
    channel_id:        str = Field(..., max_length=32)


class TicketStatusUpdate(BaseModel):
    status:     TicketStatus
    transcript: Optional[str] = Field(None, max_length=500_000)  # ~500 KB max


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_server(server_id: str, db: AsyncSession) -> Server:
    r = await db.execute(select(Server).where(Server.discord_server_id == server_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Server not found")
    return s


async def _get_or_create_user(discord_id: str, db: AsyncSession) -> User:
    r = await db.execute(select(User).where(User.discord_id == discord_id))
    u = r.scalar_one_or_none()
    if not u:
        u = User(discord_id=discord_id, username=discord_id)
        db.add(u)
        await db.flush()
    return u


# ── Ticket Type CRUD (admin dashboard) ───────────────────────────────────────

@router.get("/{server_id}/types")
async def list_ticket_types(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),   # ← guild admin guard
):
    server = await _get_server(server_id, db)
    r = await db.execute(
        select(TicketType).where(TicketType.server_id == server.id)
    )
    types = r.scalars().all()
    return [
        {
            "id":                 t.id,
            "ticket_name":        t.ticket_name,
            "ticket_description": t.ticket_description,
            "ticket_category_id": t.ticket_category_id,
            "staff_role_id":      t.staff_role_id,
            "panel_message":      t.panel_message,
            "button_label":       t.button_label,
            "button_emoji":       t.button_emoji,
        }
        for t in types
    ]


@router.post("/{server_id}/types")
async def create_ticket_type(
    server_id: str,
    payload: TicketTypeCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),   # ← guild admin guard
):
    server = await _get_server(server_id, db)
    tt = TicketType(server_id=server.id, **payload.dict())
    db.add(tt)
    await db.flush()
    return {"id": tt.id, "ticket_name": tt.ticket_name}


@router.put("/{server_id}/types/{type_id}")
async def update_ticket_type(
    server_id: str,
    type_id: int,
    payload: TicketTypeCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),   # ← guild admin guard
):
    server = await _get_server(server_id, db)
    r = await db.execute(
        select(TicketType).where(TicketType.id == type_id, TicketType.server_id == server.id)
    )
    tt = r.scalar_one_or_none()
    if not tt:
        raise HTTPException(404, "Ticket type not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(tt, k, v)
    return {"ok": True}


@router.delete("/{server_id}/types/{type_id}")
async def delete_ticket_type(
    server_id: str,
    type_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),   # ← guild admin guard
):
    server = await _get_server(server_id, db)
    r = await db.execute(
        select(TicketType).where(TicketType.id == type_id, TicketType.server_id == server.id)
    )
    tt = r.scalar_one_or_none()
    if not tt:
        raise HTTPException(404, "Ticket type not found")
    await db.delete(tt)
    return {"ok": True}


# ── Ticket list (admin dashboard) ─────────────────────────────────────────────

@router.get("/{server_id}/list")
async def list_tickets(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),   # ← guild admin guard
):
    server = await _get_server(server_id, db)
    r = await db.execute(
        select(Ticket)
        .where(Ticket.server_id == server.id)
        .options(selectinload(Ticket.ticket_type), selectinload(Ticket.user))
        .order_by(Ticket.created_at.desc())
        .limit(200)
    )
    tickets = r.scalars().all()
    return [
        {
            "id":         t.id,
            "serial":     t.serial,
            "status":     t.status,
            "channel_id": t.channel_id,
            "type_name":  t.ticket_type.ticket_name if t.ticket_type else None,
            "user":       t.user.username if t.user else None,
            "created_at": t.created_at.isoformat(),
        }
        for t in tickets
    ]


# ── Bot-facing endpoints (API key protected) ──────────────────────────────────

@router.post("/create", dependencies=[Depends(require_bot_api_key)])
async def bot_create_ticket(
    payload: TicketCreate,
    db: AsyncSession = Depends(get_db),
):
    """Bot calls this after creating the Discord channel to record the ticket."""
    server = await _get_server(payload.server_discord_id, db)
    user   = await _get_or_create_user(payload.user_discord_id, db)

    # Atomically increment per-server counter (SELECT FOR UPDATE prevents duplicate serials)
    r = await db.execute(
        select(TicketCounter)
        .where(
            TicketCounter.server_id      == server.id,
            TicketCounter.ticket_type_id == payload.ticket_type_id,
        )
        .with_for_update()          # ← prevents race condition
    )
    counter = r.scalar_one_or_none()
    if not counter:
        counter = TicketCounter(
            server_id=server.id,
            ticket_type_id=payload.ticket_type_id,
            counter=0,
        )
        db.add(counter)
        await db.flush()

    counter.counter += 1
    serial = counter.counter

    ticket = Ticket(
        server_id      = server.id,
        ticket_type_id = payload.ticket_type_id,
        user_id        = user.id,
        channel_id     = payload.channel_id,
        serial         = serial,
        status         = TicketStatus.open,
    )
    db.add(ticket)
    await db.flush()
    return {"ticket_id": ticket.id, "serial": serial}


@router.patch("/update/{ticket_id}", dependencies=[Depends(require_bot_api_key)])
async def bot_update_ticket(
    ticket_id: int,
    payload: TicketStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Bot calls this to update ticket status."""
    r = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = r.scalar_one_or_none()
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    ticket.status = payload.status
    if payload.transcript:
        ticket.transcript = payload.transcript
    if payload.status == TicketStatus.closed:
        ticket.closed_at = datetime.now(timezone.utc)
    return {"ok": True}


@router.get("/config/{server_id}", dependencies=[Depends(require_bot_api_key)])
async def bot_get_config(
    server_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Bot fetches all ticket type configs for a guild."""
    server = await _get_server(server_id, db)
    r = await db.execute(
        select(TicketType).where(TicketType.server_id == server.id)
    )
    types = r.scalars().all()
    return [
        {
            "id":                 t.id,
            "ticket_name":        t.ticket_name,
            "ticket_category_id": t.ticket_category_id,
            "staff_role_id":      t.staff_role_id,
            "panel_message":      t.panel_message,
        }
        for t in types
    ]
