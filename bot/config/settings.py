import os
from dataclasses import dataclass


@dataclass
class BotSettings:
    discord_token: str = os.getenv("DISCORD_BOT_TOKEN", "")
    api_base_url: str = os.getenv("API_BASE_URL", "http://api:8000")


settings = BotSettings()
