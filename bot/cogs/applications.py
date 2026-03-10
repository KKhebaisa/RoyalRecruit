import discord
from discord import app_commands
from discord.ext import commands

from bot.services.api_client import APIClient


class ApplicationsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="approve", description="Approve an application")
    async def approve(self, interaction: discord.Interaction):
        await interaction.response.send_message("Application approved.", ephemeral=True)

    @app_commands.command(name="reject", description="Reject an application")
    async def reject(self, interaction: discord.Interaction):
        await interaction.response.send_message("Application rejected.", ephemeral=True)

    async def run_application_flow(self, interaction: discord.Interaction, app_config: dict):
        guild = interaction.guild
        member = interaction.user
        channel_name = f"application-{app_config['application_name'].lower().replace(' ', '-')}-{member.name.lower()}"
        category = guild.get_channel(int(app_config["category_channel"]))
        channel = await guild.create_text_channel(channel_name[:100], category=category)

        answers: dict[str, str] = {}
        await channel.send(f"{member.mention} Starting **{app_config['application_name']}**")

        def check(message: discord.Message) -> bool:
            return message.author.id == member.id and message.channel.id == channel.id

        for question in app_config["questions"]:
            await channel.send(question)
            response = await self.bot.wait_for("message", check=check, timeout=600)
            answers[question] = response.content

        await channel.send("Thank you for completing the application. Leadership will review your submission.")
        await self.api.submit_application(guild.id, app_config["application_name"], member.id, answers)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ApplicationsCog(bot))
