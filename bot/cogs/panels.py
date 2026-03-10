import discord
from discord.ext import commands

from bot.services.api_client import APIClient


class TicketButton(discord.ui.Button):
    def __init__(self, label: str, staff_role_id: int, ticket_type: str):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.staff_role_id = staff_role_id
        self.ticket_type = ticket_type

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        api = APIClient()
        category = discord.utils.get(guild.categories, name="Tickets")
        if category is None:
            category = await guild.create_category("Tickets")

        temp = await api.create_ticket(guild.id, self.ticket_type, member.id, 0)
        serial = temp.get("serial", "000")
        channel_name = f"ticket-{self.ticket_type.lower().replace(' ', '-')}-{serial}"[:100]

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        staff_role = guild.get_role(self.staff_role_id)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)
        await api.log_event(guild.id, "ticket_opened", {"ticket_type": self.ticket_type, "channel_id": channel.id, "user_id": member.id})
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)


class TicketPanelView(discord.ui.View):
    def __init__(self, configs: list[dict]):
        super().__init__(timeout=None)
        for conf in configs:
            self.add_item(TicketButton(conf["ticket_name"], int(conf["staff_role"]), conf["ticket_name"]))


class PanelsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.api = APIClient()

    @commands.command(name="send_ticket_panel")
    @commands.has_permissions(administrator=True)
    async def send_ticket_panel(self, ctx: commands.Context):
        configs = await self.api.get_ticket_configs(ctx.guild.id)
        if not configs:
            await ctx.send("No ticket configurations found.")
            return
        embed = discord.Embed(title="Support Center", description="Select the request type.")
        await ctx.send(embed=embed, view=TicketPanelView(configs))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PanelsCog(bot))
