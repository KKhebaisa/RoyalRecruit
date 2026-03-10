import discord
from discord import app_commands
from discord.ext import commands

from bot.services.api_client import APIClient


class TicketsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="close", description="Close the current ticket")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("Ticket closed.", ephemeral=True)

    @app_commands.command(name="lock", description="Lock the current ticket channel")
    async def lock(self, interaction: discord.Interaction):
        await interaction.response.send_message("Ticket locked.", ephemeral=True)

    @app_commands.command(name="adduser", description="Add a user to this ticket")
    async def adduser(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.channel.set_permissions(user, view_channel=True, send_messages=True)
        await interaction.response.send_message(f"Added {user.mention}.", ephemeral=True)

    @app_commands.command(name="removeuser", description="Remove a user from this ticket")
    async def removeuser(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.channel.set_permissions(user, overwrite=None)
        await interaction.response.send_message(f"Removed {user.mention}.", ephemeral=True)

    @app_commands.command(name="transcript", description="Create a transcript placeholder")
    async def transcript(self, interaction: discord.Interaction):
        await interaction.response.send_message("Transcript generation queued.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TicketsCog(bot))
