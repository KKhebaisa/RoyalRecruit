"""
Panels cog.
Staff command to deploy a panel embed + buttons into a Discord channel.
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs.tickets      import TicketOpenView
from cogs.applications import ApplicationOpenView

logger = logging.getLogger(__name__)


class PanelsCog(commands.Cog, name="Panels"):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sendpanel", description="Send a configured panel to this channel.")
    @app_commands.describe(panel_id="The panel ID from the dashboard")
    @app_commands.default_permissions(manage_guild=True)
    async def sendpanel_cmd(self, interaction: discord.Interaction, panel_id: int):
        """Fetch panel config from API and post the embed + buttons."""
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        try:
            panels = await self.bot.api.get_panels(str(guild.id))
        except Exception as e:
            logger.error(f"Failed to fetch panels: {e}")
            await interaction.followup.send("❌ Could not load panel configuration.", ephemeral=True)
            return

        panel = next((p for p in panels if p["id"] == panel_id), None)
        if not panel:
            await interaction.followup.send(f"❌ Panel {panel_id} not found.", ephemeral=True)
            return

        # Build embed
        embed = discord.Embed(
            title=panel["title"],
            description=panel.get("description") or "",
            color=panel.get("color") or 0x5865F2,
        )

        # Build the correct view
        panel_type = panel.get("panel_type", "ticket")
        if panel_type == "ticket":
            view = TicketOpenView(panel.get("ticket_types", []))
        else:
            view = ApplicationOpenView(panel.get("application_types", []))

        msg = await interaction.channel.send(embed=embed, view=view)

        # Store message_id in API
        try:
            await self.bot.api.update_panel_message_id(panel_id, str(msg.id))
        except Exception as e:
            logger.warning(f"Failed to update panel message_id: {e}")

        await interaction.followup.send(
            f"✅ Panel sent to {interaction.channel.mention}", ephemeral=True
        )

    @app_commands.command(name="listpanels", description="List all configured panels for this server.")
    @app_commands.default_permissions(manage_guild=True)
    async def listpanels_cmd(self, interaction: discord.Interaction):
        """List panels configured for this guild."""
        await interaction.response.defer(ephemeral=True)
        try:
            panels = await self.bot.api.get_panels(str(interaction.guild.id))
        except Exception as e:
            await interaction.followup.send("❌ Could not load panels.", ephemeral=True)
            return

        if not panels:
            await interaction.followup.send("No panels configured. Create one in the dashboard.", ephemeral=True)
            return

        lines = [f"**ID {p['id']}** – {p['title']} (`{p['panel_type']}`)" for p in panels]
        embed = discord.Embed(
            title="📋 Configured Panels",
            description="\n".join(lines),
            color=0x5865F2,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(PanelsCog(bot))
