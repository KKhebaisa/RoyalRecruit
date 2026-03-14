"""
RoyalRecruit Discord Bot
Entry point – initialises the bot and loads all cogs.
"""

import asyncio
import logging

import discord
from discord.ext import commands

from config.settings import load_config
from services.api_client import APIClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("royalrecruit")

COGS = [
    "cogs.events",
    "cogs.tickets",
    "cogs.applications",
    "cogs.panels",
    "cogs.meta",        # /help, /invite, /ping, /stats + top.gg posting
]

INTENTS = discord.Intents.default()
INTENTS.message_content = True   # Privileged – requires approval in Discord Dev Portal
INTENTS.guilds          = True
INTENTS.members         = True   # Privileged – requires approval in Discord Dev Portal


class RoyalRecruitBot(commands.Bot):
    """Custom bot subclass – holds shared resources."""

    def __init__(self, api_client: APIClient, config):
        super().__init__(
            command_prefix="\x00",   # Slash commands only; null prefix disables prefix commands
            intents=INTENTS,
            help_command=None,
        )
        self.api:    APIClient = api_client
        self.config            = config

    async def setup_hook(self):
        """Load all cogs and sync slash commands."""
        for cog in COGS:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}", exc_info=True)

        # Smart sync: guild-scoped in dev (instant), global in production (up to 1 hour)
        if self.config.DEV_GUILD_ID:
            dev_guild = discord.Object(id=self.config.DEV_GUILD_ID)
            self.tree.copy_global_to(guild=dev_guild)
            await self.tree.sync(guild=dev_guild)
            logger.info(f"Slash commands synced to dev guild {self.config.DEV_GUILD_ID}.")
        else:
            await self.tree.sync()
            logger.info("Slash commands synced globally.")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Serving {len(self.guilds)} guilds")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="your applications 👑",
            )
        )

    async def close(self):
        await self.api.close()
        await super().close()


async def main():
    config     = load_config()
    api_client = APIClient(config.API_BASE_URL, config.API_SECRET_KEY)
    bot        = RoyalRecruitBot(api_client, config)

    async with bot:
        await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
