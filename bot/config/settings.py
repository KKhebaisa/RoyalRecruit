"""
Bot configuration loaded from environment variables.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BotConfig:
    BOT_TOKEN:          str
    API_BASE_URL:       str
    API_SECRET_KEY:     str
    DISCORD_CLIENT_ID:  str = ""
    TOPGG_TOKEN:        Optional[str] = None
    SUPPORT_SERVER_URL: str = ""
    PRIVACY_POLICY_URL: str = ""
    BOT_INVITE_URL:     str = ""
    DEV_GUILD_ID:       Optional[int] = None
    ENVIRONMENT:        str = "production"


def load_config() -> BotConfig:
    dev_guild_raw = os.getenv("DEV_GUILD_ID")
    return BotConfig(
        BOT_TOKEN          = os.environ["DISCORD_BOT_TOKEN"],
        API_BASE_URL       = os.getenv("BOT_API_BASE_URL", "http://api:8000"),
        API_SECRET_KEY     = os.environ["API_SECRET_KEY"],
        DISCORD_CLIENT_ID  = os.getenv("DISCORD_CLIENT_ID", ""),
        TOPGG_TOKEN        = os.getenv("TOPGG_TOKEN"),
        SUPPORT_SERVER_URL = os.getenv("SUPPORT_SERVER_URL", ""),
        PRIVACY_POLICY_URL = os.getenv("PRIVACY_POLICY_URL", ""),
        BOT_INVITE_URL     = os.getenv("BOT_INVITE_URL", ""),
        DEV_GUILD_ID       = int(dev_guild_raw) if dev_guild_raw else None,
        ENVIRONMENT        = os.getenv("ENVIRONMENT", "production"),
    )
