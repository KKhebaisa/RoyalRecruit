"""
RoyalRecruit – Authentication & Security Utilities.

Covers:
  - JWT creation / validation
  - Discord OAuth2 token exchange & API calls
  - Discord token encryption (Fernet AES-128)
  - Bot API-key guard (timing-safe)
  - Guild admin permission guard (prevents cross-server access)
"""

import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
import jwt
from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings

logger = logging.getLogger(__name__)

DISCORD_API_BASE = "https://discord.com/api/v10"
ADMINISTRATOR_BIT = 0x8  # Discord permission bit

# ─────────────────────────────────────────────────────────────────────────────
# Fernet cipher for Discord token encryption at rest
# ─────────────────────────────────────────────────────────────────────────────

_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    """Return (cached) Fernet instance built from TOKEN_ENCRYPTION_KEY."""
    global _fernet
    if _fernet is None:
        key = settings.TOKEN_ENCRYPTION_KEY
        if not key:
            raise RuntimeError("TOKEN_ENCRYPTION_KEY is not set in environment.")
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_token(token: str) -> str:
    """Encrypt a Discord OAuth token for safe storage in the database."""
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """Decrypt a stored Discord OAuth token. Raises HTTPException on failure."""
    try:
        return _get_fernet().decrypt(encrypted.encode()).decode()
    except InvalidToken:
        raise HTTPException(status_code=401, detail="Stored token is corrupt or key changed.")


# ─────────────────────────────────────────────────────────────────────────────
# Bearer scheme (shared instance)
# ─────────────────────────────────────────────────────────────────────────────

_bearer = HTTPBearer()


# ─────────────────────────────────────────────────────────────────────────────
# JWT helpers
# ─────────────────────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> str:
    """FastAPI dependency: extract discord_id from JWT bearer token."""
    payload = decode_access_token(credentials.credentials)
    discord_id: Optional[str] = payload.get("sub")
    if not discord_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return discord_id


# ─────────────────────────────────────────────────────────────────────────────
# Guild admin permission guard (prevents cross-server access!)
# ─────────────────────────────────────────────────────────────────────────────

async def require_guild_admin(
    server_id: str,
    discord_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(lambda: None),  # injected properly via closure below
) -> str:
    """
    Verifies the current JWT user has ADMINISTRATOR permission in the given
    Discord guild. Must be used via the factory below to inject the DB session.
    Returns the discord_id on success.
    """
    # Import here to avoid circular imports
    from database.connection import get_db
    from models import User

    # This function is used via make_guild_admin_dep() — see below.
    raise NotImplementedError("Use make_guild_admin_dep() instead.")


def make_guild_admin_dep():
    """
    Returns a FastAPI dependency that checks the current user has ADMINISTRATOR
    permission in the guild identified by the `server_id` path parameter.

    Usage in a router:
        @router.get("/{server_id}/foo")
        async def endpoint(
            server_id: str,
            _: str = Depends(make_guild_admin_dep()),
            db: AsyncSession = Depends(get_db),
        ):
            ...
    """
    from database.connection import get_db
    from models import User

    async def _check(
        server_id: str,
        credentials: HTTPAuthorizationCredentials = Security(_bearer),
        db: AsyncSession = Depends(get_db),
    ) -> str:
        payload = decode_access_token(credentials.credentials)
        discord_id: Optional[str] = payload.get("sub")
        if not discord_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Fetch stored (encrypted) access token
        result = await db.execute(select(User).where(User.discord_id == discord_id))
        user = result.scalar_one_or_none()
        if not user or not user.access_token:
            raise HTTPException(status_code=401, detail="No Discord credentials stored. Re-login.")

        try:
            discord_access_token = decrypt_token(user.access_token)
        except HTTPException:
            raise HTTPException(status_code=401, detail="Token decryption failed. Re-login.")

        # Fetch guilds from Discord
        guilds = await get_discord_guilds(discord_access_token)

        # Find the specific guild
        guild = next(
            (g for g in guilds if str(g["id"]) == str(server_id)),
            None,
        )
        if not guild:
            raise HTTPException(status_code=403, detail="You are not a member of this server.")

        permissions = int(guild.get("permissions", "0"))
        if not (permissions & ADMINISTRATOR_BIT):
            raise HTTPException(
                status_code=403,
                detail="You must have ADMINISTRATOR permission in this server.",
            )

        return discord_id

    return _check


# ─────────────────────────────────────────────────────────────────────────────
# Internal bot API key guard (timing-safe)
# ─────────────────────────────────────────────────────────────────────────────

async def require_bot_api_key(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> None:
    """Guard internal bot→API endpoints with a shared secret (timing-safe)."""
    if not hmac.compare_digest(credentials.credentials, settings.API_SECRET_KEY):
        raise HTTPException(status_code=403, detail="Invalid API key")


# ─────────────────────────────────────────────────────────────────────────────
# Discord OAuth2 helpers
# ─────────────────────────────────────────────────────────────────────────────

async def exchange_code_for_token(code: str) -> dict:
    """Exchange Discord OAuth2 code for access/refresh tokens."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{DISCORD_API_BASE}/oauth2/token",
                data={
                    "client_id":     settings.DISCORD_CLIENT_ID,
                    "client_secret": settings.DISCORD_CLIENT_SECRET,
                    "grant_type":    "authorization_code",
                    "code":          code,
                    "redirect_uri":  settings.DISCORD_REDIRECT_URI,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("Discord token exchange failed: %s", exc.response.text)
        raise HTTPException(status_code=502, detail="Discord OAuth failed. Please try again.")
    except httpx.RequestError as exc:
        logger.error("Discord API unreachable: %s", exc)
        raise HTTPException(status_code=502, detail="Discord API is currently unreachable.")


async def refresh_discord_token(refresh_token: str) -> dict:
    """Refresh a Discord access token using the refresh token."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{DISCORD_API_BASE}/oauth2/token",
                data={
                    "client_id":     settings.DISCORD_CLIENT_ID,
                    "client_secret": settings.DISCORD_CLIENT_SECRET,
                    "grant_type":    "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("Discord token refresh failed: %s", exc.response.text)
        raise HTTPException(status_code=401, detail="Session expired. Please re-login.")
    except httpx.RequestError as exc:
        logger.error("Discord API unreachable: %s", exc)
        raise HTTPException(status_code=502, detail="Discord API is currently unreachable.")


async def get_discord_user(access_token: str) -> dict:
    """Fetch the authenticated user's Discord profile."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DISCORD_API_BASE}/users/@me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("Failed to fetch Discord user: %s", exc.response.text)
        raise HTTPException(status_code=502, detail="Failed to fetch Discord profile.")
    except httpx.RequestError as exc:
        logger.error("Discord API unreachable: %s", exc)
        raise HTTPException(status_code=502, detail="Discord API is currently unreachable.")


async def get_discord_guilds(access_token: str) -> list:
    """Fetch the guilds the authenticated user is a member of."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DISCORD_API_BASE}/users/@me/guilds",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("Failed to fetch Discord guilds: %s", exc.response.text)
        raise HTTPException(status_code=502, detail="Failed to fetch Discord guild list.")
    except httpx.RequestError as exc:
        logger.error("Discord API unreachable: %s", exc)
        raise HTTPException(status_code=502, detail="Discord API is currently unreachable.")
