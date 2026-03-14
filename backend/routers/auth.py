"""
Authentication router.
Handles Discord OAuth2 callback (with CSRF state validation),
JWT issuance, token refresh, and user profile endpoints.
"""

import logging
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from models import User
from auth.security import (
    exchange_code_for_token,
    refresh_discord_token,
    get_discord_user,
    get_discord_guilds,
    create_access_token,
    get_current_user_id,
    encrypt_token,
    decrypt_token,
)
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# CSRF state helpers
# ─────────────────────────────────────────────────────────────────────────────

STATE_COOKIE = "oauth_state"


@router.get("/login-url")
async def get_login_url(response: Response):
    """
    Generate a Discord OAuth2 URL with a CSRF state token.
    Returns the URL and sets an HttpOnly state cookie.
    """
    state = secrets.token_urlsafe(32)
    response.set_cookie(
        key=STATE_COOKIE,
        value=state,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=300,  # 5 minutes
    )
    params = (
        f"client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={settings.DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20guilds"
        f"&state={state}"
    )
    return {"url": f"https://discord.com/api/oauth2/authorize?{params}"}


# ─────────────────────────────────────────────────────────────────────────────
# OAuth2 callback
# ─────────────────────────────────────────────────────────────────────────────

class CallbackPayload(BaseModel):
    code: str
    state: str


@router.post("/callback")
async def discord_callback(
    payload: CallbackPayload,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange Discord OAuth2 code for our JWT.
    Validates the CSRF state cookie before proceeding.
    """
    # 1. Validate CSRF state
    cookie_state = request.cookies.get(STATE_COOKIE)
    if not cookie_state or not secrets.compare_digest(cookie_state, payload.state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state. Possible CSRF attack.")

    # Clear the state cookie immediately
    response.delete_cookie(STATE_COOKIE)

    # 2. Exchange code → Discord tokens
    token_data = await exchange_code_for_token(payload.code)
    discord_access_token  = token_data["access_token"]
    discord_refresh_token = token_data.get("refresh_token", "")

    # 3. Fetch Discord user profile
    discord_user = await get_discord_user(discord_access_token)

    # 4. Encrypt tokens before storing
    encrypted_access  = encrypt_token(discord_access_token)
    encrypted_refresh = encrypt_token(discord_refresh_token) if discord_refresh_token else None

    # 5. Upsert user in database
    result = await db.execute(
        select(User).where(User.discord_id == discord_user["id"])
    )
    user = result.scalar_one_or_none()

    if user:
        user.username      = discord_user["username"]
        user.discriminator = discord_user.get("discriminator")
        user.avatar        = discord_user.get("avatar")
        user.access_token  = encrypted_access
        user.refresh_token = encrypted_refresh
    else:
        user = User(
            discord_id    = discord_user["id"],
            username      = discord_user["username"],
            discriminator = discord_user.get("discriminator"),
            avatar        = discord_user.get("avatar"),
            access_token  = encrypted_access,
            refresh_token = encrypted_refresh,
        )
        db.add(user)

    await db.flush()

    # 6. Issue JWT (short-lived access token)
    jwt_token = create_access_token(
        {"sub": discord_user["id"]},
        expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
        "user": {
            "discord_id": user.discord_id,
            "username":   user.username,
            "avatar":     user.avatar,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Token refresh
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/refresh")
async def refresh_token(
    db: AsyncSession = Depends(get_db),
    discord_id: str = Depends(get_current_user_id),
):
    """
    Silently refresh the Discord access token using the stored refresh token,
    and return a new JWT.
    """
    result = await db.execute(select(User).where(User.discord_id == discord_id))
    user = result.scalar_one_or_none()
    if not user or not user.refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token. Please re-login.")

    decrypted_refresh = decrypt_token(user.refresh_token)
    new_token_data    = await refresh_discord_token(decrypted_refresh)

    # Update stored tokens
    user.access_token  = encrypt_token(new_token_data["access_token"])
    if new_token_data.get("refresh_token"):
        user.refresh_token = encrypt_token(new_token_data["refresh_token"])

    # Issue new JWT
    jwt_token = create_access_token(
        {"sub": discord_id},
        expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Profile & guild endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/me")
async def get_me(
    db: AsyncSession = Depends(get_db),
    discord_id: str = Depends(get_current_user_id),
):
    """Return the currently authenticated user's profile."""
    result = await db.execute(select(User).where(User.discord_id == discord_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "discord_id":    user.discord_id,
        "username":      user.username,
        "discriminator": user.discriminator,
        "avatar":        user.avatar,
    }


@router.get("/guilds")
async def get_my_guilds(
    db: AsyncSession = Depends(get_db),
    discord_id: str = Depends(get_current_user_id),
):
    """Return guilds where the user has ADMINISTRATOR permission (bit 0x8)."""
    result = await db.execute(select(User).where(User.discord_id == discord_id))
    user = result.scalar_one_or_none()
    if not user or not user.access_token:
        raise HTTPException(status_code=401, detail="No Discord token stored")

    decrypted = decrypt_token(user.access_token)
    guilds     = await get_discord_guilds(decrypted)

    ADMINISTRATOR_BIT = 0x8
    admin_guilds = [
        g for g in guilds
        if int(g.get("permissions", "0")) & ADMINISTRATOR_BIT
    ]
    return admin_guilds
