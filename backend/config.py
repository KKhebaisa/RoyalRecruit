"""
RoyalRecruit Backend – Configuration.
All settings are loaded from environment variables via pydantic-settings.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://royalrecruit:password@postgres:5432/royalrecruit"
    )

    # ── Discord OAuth2 / Bot ──────────────────────────────────────────────────
    DISCORD_CLIENT_ID: str = ""
    DISCORD_CLIENT_SECRET: str = ""
    DISCORD_REDIRECT_URI: str = "http://localhost:3000/api/auth/callback"
    DISCORD_BOT_TOKEN: str = ""

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60           # Reduced from 24h → 1h for security
    JWT_REFRESH_EXPIRE_DAYS: int = 30      # Refresh token lifetime

    # ── Discord Token Encryption (Fernet) ─────────────────────────────────────
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    TOKEN_ENCRYPTION_KEY: str = ""

    # ── Internal API ──────────────────────────────────────────────────────────
    API_SECRET_KEY: str = "internal-api-secret-change-me"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # ── Bot → API ─────────────────────────────────────────────────────────────
    BOT_API_BASE_URL: str = "http://api:8000"

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_AUTH: str = "5/minute"        # OAuth callback
    RATE_LIMIT_DEFAULT: str = "30/minute"    # General API endpoints
    RATE_LIMIT_WRITE: str = "10/minute"      # POST/PUT/DELETE endpoints

    # ── Discord Bot Listing ───────────────────────────────────────────────────
    TOPGG_TOKEN: Optional[str] = None        # top.gg API token for stats posting
    SUPPORT_SERVER_URL: str = ""             # Your Discord support server invite
    PRIVACY_POLICY_URL: str = ""             # Hosted privacy policy URL
    BOT_INVITE_URL: str = ""                 # Bot invite OAuth2 URL from Discord Dev Portal

    # ── Development ───────────────────────────────────────────────────────────
    DEV_GUILD_ID: Optional[int] = None       # Set to guild ID for instant slash cmd sync in dev
    ENVIRONMENT: str = "production"          # "development" | "production"

    class Config:
        env_file = ".env"


settings = Settings()
