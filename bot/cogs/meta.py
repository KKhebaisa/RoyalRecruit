"""
Meta cog – required for Discord bot listing sites.
Provides: /help, /invite, /ping
Provides: automatic top.gg guild count posting every 30 minutes.
"""

import logging
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from config.settings import load_config

logger = logging.getLogger(__name__)


class MetaCog(commands.Cog, name="Meta"):

    def __init__(self, bot):
        self.bot    = bot
        self.config = load_config()
        if self.config.TOPGG_TOKEN and AIOHTTP_AVAILABLE:
            self._post_guild_count.start()

    def cog_unload(self):
        self._post_guild_count.cancel()

    # ── Background task: post guild count to top.gg ──────────────────────────

    @tasks.loop(minutes=30)
    async def _post_guild_count(self):
        """Post server count to top.gg (required for listing)."""
        if not self.config.TOPGG_TOKEN:
            return
        url     = f"https://top.gg/api/bots/{self.bot.user.id}/stats"
        payload = {"server_count": len(self.bot.guilds)}
        headers = {"Authorization": self.config.TOPGG_TOKEN}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        logger.info(f"Posted guild count ({len(self.bot.guilds)}) to top.gg.")
                    else:
                        logger.warning(f"top.gg stats post returned {resp.status}")
        except Exception as e:
            logger.error(f"Failed to post guild count to top.gg: {e}")

    @_post_guild_count.before_loop
    async def _before_post(self):
        await self.bot.wait_until_ready()

    # ── Slash commands ────────────────────────────────────────────────────────

    @app_commands.command(name="ping", description="Check the bot's latency.")
    async def ping_cmd(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"WebSocket latency: **{latency_ms}ms**",
            color=0x5865F2,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="invite", description="Get a link to invite RoyalRecruit to your server.")
    async def invite_cmd(self, interaction: discord.Interaction):
        invite_url = self.config.BOT_INVITE_URL or (
            f"https://discord.com/oauth2/authorize"
            f"?client_id={self.config.DISCORD_CLIENT_ID}"
            f"&permissions=536879120"
            f"&scope=bot%20applications.commands"
        )
        embed = discord.Embed(
            title="👑 Invite RoyalRecruit",
            description=(
                f"[**Click here to invite me**]({invite_url}) to your server!\n\n"
                "I'll set up ticket systems and application flows in minutes."
            ),
            color=0xFEE75C,
        )
        if self.config.SUPPORT_SERVER_URL:
            embed.add_field(
                name="💬 Support Server",
                value=f"[Join here]({self.config.SUPPORT_SERVER_URL})",
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="help", description="Learn what RoyalRecruit can do.")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="👑 RoyalRecruit — Help",
            description=(
                "RoyalRecruit lets server admins create **ticket systems** and "
                "**application systems** with a web dashboard. Users interact via Discord buttons."
            ),
            color=0x5865F2,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name="🎫 Ticket Commands",
            value=(
                "`/close` — Close the current ticket\n"
                "`/lock` — Lock the ticket (read-only)\n"
                "`/adduser` — Add a user to the ticket\n"
                "`/removeuser` — Remove a user from the ticket\n"
                "`/transcript` — Download a text transcript"
            ),
            inline=False,
        )
        embed.add_field(
            name="📋 Application Commands",
            value=(
                "`/approve <id>` — Approve an application\n"
                "`/reject <id>` — Reject an application"
            ),
            inline=False,
        )
        embed.add_field(
            name="⚙️ Dashboard",
            value="Configure everything at the web dashboard. Log in with Discord OAuth.",
            inline=False,
        )
        embed.add_field(
            name="📜 Links",
            value="\n".join(filter(None, [
                f"[Privacy Policy]({self.config.PRIVACY_POLICY_URL})" if self.config.PRIVACY_POLICY_URL else None,
                f"[Support Server]({self.config.SUPPORT_SERVER_URL})" if self.config.SUPPORT_SERVER_URL else None,
                f"[Invite Me]({self.config.BOT_INVITE_URL})" if self.config.BOT_INVITE_URL else None,
            ])) or "*(Not configured yet)*",
            inline=False,
        )
        embed.set_footer(text=f"RoyalRecruit • {len(self.bot.guilds)} servers")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="stats", description="View bot statistics.")
    async def stats_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📊 RoyalRecruit Stats",
            color=0x5865F2,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(MetaCog(bot))
