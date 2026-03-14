"""
HTTP client for the bot to communicate with the backend API.
All requests are authenticated with the internal API_SECRET_KEY.
"""

import logging
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class APIClient:
    """Thin async HTTP wrapper around the RoyalRecruit REST API."""

    def __init__(self, base_url: str, secret_key: str):
        self.base_url   = base_url.rstrip("/")
        self.secret_key = secret_key
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type":  "application/json",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self.headers)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def get(self, path: str, **kwargs) -> Any:
        session = await self._get_session()
        async with session.get(f"{self.base_url}{path}", **kwargs) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def post(self, path: str, json: dict = None, **kwargs) -> Any:
        session = await self._get_session()
        async with session.post(f"{self.base_url}{path}", json=json, **kwargs) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def patch(self, path: str, json: dict = None, **kwargs) -> Any:
        session = await self._get_session()
        async with session.patch(f"{self.base_url}{path}", json=json, **kwargs) as resp:
            resp.raise_for_status()
            return await resp.json()

    # ── Convenience methods ───────────────────────────────────────────────────

    async def upsert_server(self, discord_server_id: str, name: str,
                            icon: str, owner_discord_id: str) -> dict:
        return await self.post("/api/guilds/upsert", json={
            "discord_server_id": discord_server_id,
            "name":              name,
            "icon":              icon,
            "owner_discord_id":  owner_discord_id,
        })

    async def get_ticket_configs(self, server_id: str) -> list:
        return await self.get(f"/api/tickets/config/{server_id}")

    async def create_ticket(self, server_discord_id: str, ticket_type_id: int,
                            user_discord_id: str, channel_id: str) -> dict:
        return await self.post("/api/tickets/create", json={
            "server_discord_id": server_discord_id,
            "ticket_type_id":    ticket_type_id,
            "user_discord_id":   user_discord_id,
            "channel_id":        channel_id,
        })

    async def update_ticket(self, ticket_id: int, status: str,
                            transcript: str = None) -> dict:
        payload = {"status": status}
        if transcript:
            payload["transcript"] = transcript
        return await self.patch(f"/api/tickets/update/{ticket_id}", json=payload)

    async def get_application_configs(self, server_id: str) -> list:
        return await self.get(f"/api/applications/config/{server_id}")

    async def create_application(self, server_discord_id: str,
                                 application_type_id: int,
                                 user_discord_id: str,
                                 channel_id: str,
                                 answers: dict) -> dict:
        return await self.post("/api/applications/create", json={
            "server_discord_id":   server_discord_id,
            "application_type_id": application_type_id,
            "user_discord_id":     user_discord_id,
            "channel_id":          channel_id,
            "answers":             answers,
        })

    async def review_application(self, application_id: int, status: str,
                                 reviewer_discord_id: str,
                                 review_note: str = None) -> dict:
        return await self.patch(f"/api/applications/review/{application_id}", json={
            "status":              status,
            "reviewer_discord_id": reviewer_discord_id,
            "review_note":         review_note,
        })

    async def get_panels(self, server_id: str) -> list:
        return await self.get(f"/api/panels/bot/{server_id}")

    async def update_panel_message_id(self, panel_id: int, message_id: str) -> dict:
        return await self.patch(f"/api/panels/{panel_id}/message_id", json={
            "message_id": message_id,
        })

    async def log_event(self, server_discord_id: str, event_type: str,
                        actor_discord_id: str = None,
                        target_discord_id: str = None,
                        details: dict = None) -> dict:
        return await self.post("/api/logs/", json={
            "server_discord_id": server_discord_id,
            "event_type":        event_type,
            "actor_discord_id":  actor_discord_id,
            "target_discord_id": target_discord_id,
            "details":           details,
        })
