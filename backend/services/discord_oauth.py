import httpx

from backend.core.config import get_settings

DISCORD_API = "https://discord.com/api/v10"


async def exchange_code(code: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{DISCORD_API}/oauth2/token",
            data={
                "client_id": settings.discord_client_id,
                "client_secret": settings.discord_client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.discord_redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()


async def fetch_discord_user(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        user = await client.get(f"{DISCORD_API}/users/@me", headers={"Authorization": f"Bearer {access_token}"})
        guilds = await client.get(f"{DISCORD_API}/users/@me/guilds", headers={"Authorization": f"Bearer {access_token}"})
        user.raise_for_status()
        guilds.raise_for_status()
        return {"user": user.json(), "guilds": guilds.json()}
