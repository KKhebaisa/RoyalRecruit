"""
Events cog.
Handles guild join/leave events to keep the API database in sync.
"""

import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class EventsCog(commands.Cog, name="Events"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Register/update the guild in the API when the bot joins."""
        logger.info(f"Joined guild: {guild.name} ({guild.id})")
        try:
            await self.bot.api.upsert_server(
                discord_server_id=str(guild.id),
                name=guild.name,
                icon=str(guild.icon) if guild.icon else None,
                owner_discord_id=str(guild.owner_id),
            )
        except Exception as e:
            logger.error(f"Failed to upsert server {guild.id}: {e}")

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        """Keep guild metadata in sync."""
        try:
            await self.bot.api.upsert_server(
                discord_server_id=str(after.id),
                name=after.name,
                icon=str(after.icon) if after.icon else None,
                owner_discord_id=str(after.owner_id),
            )
        except Exception as e:
            logger.error(f"Failed to update server {after.id}: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Sync all current guilds on startup."""
        for guild in self.bot.guilds:
            try:
                await self.bot.api.upsert_server(
                    discord_server_id=str(guild.id),
                    name=guild.name,
                    icon=str(guild.icon) if guild.icon else None,
                    owner_discord_id=str(guild.owner_id),
                )
            except Exception as e:
                logger.error(f"Failed to sync guild {guild.id}: {e}")
        logger.info(f"Synced {len(self.bot.guilds)} guild(s) with API.")


async def setup(bot):
    await bot.add_cog(EventsCog(bot))
