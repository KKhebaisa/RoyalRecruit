import httpx

from bot.config.settings import settings


class APIClient:
    def __init__(self) -> None:
        self.base_url = settings.api_base_url

    async def get_ticket_configs(self, guild_id: int) -> list[dict]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.base_url}/tickets/config/{guild_id}")
            response.raise_for_status()
            return response.json()

    async def create_ticket(self, guild_id: int, ticket_type: str, user_id: int, channel_id: int) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/tickets/",
                json={"discord_server_id": str(guild_id), "type": ticket_type, "user_id": str(user_id), "channel_id": str(channel_id)},
            )
            response.raise_for_status()
            return response.json()

    async def get_application_types(self, guild_id: int) -> list[dict]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.base_url}/applications/types/{guild_id}")
            response.raise_for_status()
            return response.json()

    async def submit_application(self, guild_id: int, app_type: str, user_id: int, answers: dict) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/applications/submit",
                json={"discord_server_id": str(guild_id), "type": app_type, "user_id": str(user_id), "answers": answers},
            )
            response.raise_for_status()
            return response.json()

    async def log_event(self, guild_id: int, event_type: str, details: dict) -> None:
        async with httpx.AsyncClient(timeout=20) as client:
            await client.post(
                f"{self.base_url}/logs/",
                json={"discord_server_id": str(guild_id), "event_type": event_type, "details": details},
            )
