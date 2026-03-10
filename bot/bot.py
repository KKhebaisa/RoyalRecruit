import discord
from discord.ext import commands

from bot.config.settings import settings

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True


class RoyalRecruitBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=INTENTS)

    async def setup_hook(self) -> None:
        for extension in [
            "bot.cogs.events",
            "bot.cogs.tickets",
            "bot.cogs.applications",
            "bot.cogs.panels",
        ]:
            await self.load_extension(extension)
        await self.tree.sync()


bot = RoyalRecruitBot()

if __name__ == "__main__":
    if not settings.discord_token:
        raise RuntimeError("DISCORD_BOT_TOKEN is required")
    bot.run(settings.discord_token)
