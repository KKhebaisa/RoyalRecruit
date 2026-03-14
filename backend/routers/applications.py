"""
Applications router.
Manages ApplicationType configurations, Questions, and Application instances.
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
from models import (
    Server, ApplicationType, Question, Application, ApplicationStatus, User
)
from auth.security import get_current_user_id, require_bot_api_key, make_guild_admin_dep

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class QuestionSchema(BaseModel):
    question_text: str = Field(..., min_length=1, max_length=500)
    order_index:   int = Field(..., ge=0)


class ApplicationTypeCreate(BaseModel):
    application_name:   str = Field(..., min_length=1, max_length=100)
    category_id:        Optional[str] = Field(None, max_length=32)
    staff_role_id:      Optional[str] = Field(None, max_length=32)
    welcome_message:    Optional[str] = Field(None, max_length=2000)
    completion_message: Optional[str] = Field(None, max_length=2000)
    button_label:       Optional[str] = Field(None, max_length=80)
    button_emoji:       Optional[str] = Field(None, max_length=50)
    questions:          List[QuestionSchema] = Field(default_factory=list, max_items=25)

    @validator("application_name")
    def name_no_special(cls, v):
        if not re.match(r"^[\w\s\-]+$", v):
            raise ValueError("Application name may only contain letters, numbers, spaces, and hyphens.")
        return v


class ApplicationCreate(BaseModel):
    """Used by bot to register a submitted application."""
    server_discord_id:   str = Field(..., max_length=32)
    application_type_id: int
    user_discord_id:     str = Field(..., max_length=32)
    channel_id:          str = Field(..., max_length=32)
    answers:             dict  # {question_id: answer_text}

    @validator("answers")
    def validate_answers(cls, v):
        for key, val in v.items():
            if not isinstance(val, str):
                raise ValueError("All answer values must be strings.")
            if len(val) > 2000:
                raise ValueError(f"Answer for question {key} exceeds 2000 characters.")
        if len(v) > 50:
            raise ValueError("Too many answers in submission.")
        return v


class ApplicationReview(BaseModel):
    status:              ApplicationStatus
    reviewer_discord_id: str = Field(..., max_length=32)
    review_note:         Optional[str] = Field(None, max_length=1000)


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


# ── Application Type CRUD (admin dashboard) ───────────────────────────────────

@router.get("/{server_id}/types")
async def list_application_types(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),   # ← guild admin guard
):
    server = await _get_server(server_id, db)
    r = await db.execute(
        select(ApplicationType)
        .where(ApplicationType.server_id == server.id)
        .options(selectinload(ApplicationType.questions))
    )
    types = r.scalars().all()
    return [
        {
            "id":                 at.id,
            "application_name":   at.application_name,
            "category_id":        at.category_id,
            "staff_role_id":      at.staff_role_id,
            "welcome_message":    at.welcome_message,
            "completion_message": at.completion_message,
            "button_label":       at.button_label,
            "button_emoji":       at.button_emoji,
            "questions": [
                {"id": q.id, "question_text": q.question_text, "order_index": q.order_index}
                for q in sorted(at.questions, key=lambda x: x.order_index)
            ],
        }
        for at in types
    ]


@router.post("/{server_id}/types")
async def create_application_type(
    server_id: str,
    payload: ApplicationTypeCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),   # ← guild admin guard
):
    server = await _get_server(server_id, db)
    questions_data = payload.questions
    at = ApplicationType(
        server_id          = server.id,
        application_name   = payload.application_name,
        category_id        = payload.category_id,
        staff_role_id      = payload.staff_role_id,
        welcome_message    = payload.welcome_message,
        completion_message = payload.completion_message,
        button_label       = payload.button_label,
        button_emoji       = payload.button_emoji,
    )
    db.add(at)
    await db.flush()

    for q in questions_data:
        db.add(Question(
            application_type_id=at.id,
            question_text=q.question_text,
            order_index=q.order_index,
        ))

    await db.flush()
    return {"id": at.id, "application_name": at.application_name}


@router.put("/{server_id}/types/{type_id}")
async def update_application_type(
    server_id: str,
    type_id: int,
    payload: ApplicationTypeCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),   # ← guild admin guard
):
    server = await _get_server(server_id, db)
    r = await db.execute(
        select(ApplicationType)
        .where(ApplicationType.id == type_id, ApplicationType.server_id == server.id)
        .options(selectinload(ApplicationType.questions))
    )
    at = r.scalar_one_or_none()
    if not at:
        raise HTTPException(404, "Application type not found")

    for k, v in payload.dict(exclude={"questions"}, exclude_unset=True).items():
        setattr(at, k, v)

    # Replace questions (delete old, insert new)
    for q in at.questions:
        await db.delete(q)
    await db.flush()

    for q in payload.questions:
        db.add(Question(
            application_type_id=at.id,
            question_text=q.question_text,
            order_index=q.order_index,
        ))

    return {"ok": True}


@router.delete("/{server_id}/types/{type_id}")
async def delete_application_type(
    server_id: str,
    type_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),   # ← guild admin guard
):
    server = await _get_server(server_id, db)
    r = await db.execute(
        select(ApplicationType)
        .where(ApplicationType.id == type_id, ApplicationType.server_id == server.id)
    )
    at = r.scalar_one_or_none()
    if not at:
        raise HTTPException(404, "Application type not found")
    await db.delete(at)
    return {"ok": True}


# ── Application list (admin dashboard) ────────────────────────────────────────

@router.get("/{server_id}/list")
async def list_applications(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(make_guild_admin_dep()),   # ← guild admin guard
):
    server = await _get_server(server_id, db)
    r = await db.execute(
        select(Application)
        .where(Application.server_id == server.id)
        .options(selectinload(Application.application_type), selectinload(Application.user))
        .order_by(Application.created_at.desc())
        .limit(200)
    )
    apps = r.scalars().all()
    return [
        {
            "id":         a.id,
            "status":     a.status,
            "type_name":  a.application_type.application_name if a.application_type else None,
            "user":       a.user.username if a.user else None,
            "answers":    a.answers,
            "created_at": a.created_at.isoformat(),
        }
        for a in apps
    ]


# ── Bot-facing endpoints (API key protected) ──────────────────────────────────

@router.post("/create", dependencies=[Depends(require_bot_api_key)])
async def bot_create_application(
    payload: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Bot submits a completed application."""
    server = await _get_server(payload.server_discord_id, db)
    user   = await _get_or_create_user(payload.user_discord_id, db)

    app = Application(
        server_id           = server.id,
        application_type_id = payload.application_type_id,
        user_id             = user.id,
        channel_id          = payload.channel_id,
        answers             = payload.answers,
        status              = ApplicationStatus.pending,
    )
    db.add(app)
    await db.flush()
    return {"application_id": app.id}


@router.patch("/review/{application_id}", dependencies=[Depends(require_bot_api_key)])
async def bot_review_application(
    application_id: int,
    payload: ApplicationReview,
    db: AsyncSession = Depends(get_db),
):
    """Bot updates application status after /approve or /reject."""
    r = await db.execute(select(Application).where(Application.id == application_id))
    app = r.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")
    app.status              = payload.status
    app.reviewer_discord_id = payload.reviewer_discord_id
    app.review_note         = payload.review_note
    app.reviewed_at         = datetime.now(timezone.utc)
    return {"ok": True}


@router.get("/config/{server_id}", dependencies=[Depends(require_bot_api_key)])
async def bot_get_config(
    server_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Bot fetches application type configs for a guild."""
    server = await _get_server(server_id, db)
    r = await db.execute(
        select(ApplicationType)
        .where(ApplicationType.server_id == server.id)
        .options(selectinload(ApplicationType.questions))
    )
    types = r.scalars().all()
    return [
        {
            "id":                 at.id,
            "application_name":   at.application_name,
            "category_id":        at.category_id,
            "staff_role_id":      at.staff_role_id,
            "welcome_message":    at.welcome_message,
            "completion_message": at.completion_message,
            "questions": [
                {"id": q.id, "question_text": q.question_text, "order_index": q.order_index}
                for q in sorted(at.questions, key=lambda x: x.order_index)
            ],
        }
        for at in types
    ]
