"""
Tickets cog.
Handles ticket button interactions, channel creation, and staff slash commands.

Security hardening:
  - Staff role check on all moderation commands
  - Channel name sanitization
  - Proper permission guard (owner/staff-only actions)
"""

import logging
import re
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


def _sanitize_channel_name(text: str) -> str:
    """Produce a Discord-safe channel name slug (max 32 chars)."""
    return re.sub(r"[^a-z0-9-]", "", text.lower().replace(" ", "-"))[:32]


async def _is_staff(interaction: discord.Interaction, staff_role_id: str | None = None) -> bool:
    """
    Return True if the user is a server administrator OR holds the staff role.
    Used to guard /close, /lock, /adduser, /removeuser, /transcript.
    """
    if interaction.user.guild_permissions.administrator:
        return True
    if staff_role_id:
        role = interaction.guild.get_role(int(staff_role_id))
        if role and role in interaction.user.roles:
            return True
    return False


async def _get_ticket_staff_role_id(channel: discord.TextChannel, bot) -> str | None:
    """
    Best-effort: look up the staff_role_id for the ticket type from the API.
    Falls back to None (so admins can still act) if lookup fails.
    """
    try:
        configs = await bot.api.get_ticket_configs(str(channel.guild.id))
    except Exception:
        return None
    # Match by channel name prefix (e.g. "ticket-recruitment-001" → "recruitment")
    slug = channel.name.removeprefix("ticket-").rsplit("-", 1)[0]
    for c in configs:
        if _sanitize_channel_name(c["ticket_name"]) == slug:
            return c.get("staff_role_id")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Persistent views
# ─────────────────────────────────────────────────────────────────────────────

class TicketControlView(discord.ui.View):
    """Persistent view attached to newly created ticket channels."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Close Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_close_btn",
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Prompt staff to confirm close."""
        staff_role_id = await _get_ticket_staff_role_id(interaction.channel, interaction.client)
        if not await _is_staff(interaction, staff_role_id):
            await interaction.response.send_message(
                "❌ Only staff members can close tickets.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "Are you sure you want to close this ticket?",
            view=ConfirmCloseView(),
            ephemeral=True,
        )


class ConfirmCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="Yes, close it", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await _close_ticket_channel(interaction)


class TicketOpenView(discord.ui.View):
    """
    Dynamic view rendered when a panel message is loaded.
    Each button corresponds to a ticket type.
    custom_id format: open_ticket:{ticket_type_id}
    """

    def __init__(self, ticket_types: list):
        super().__init__(timeout=None)
        for tt in ticket_types:
            label     = tt.get("button_label") or tt["ticket_name"]
            custom_id = f"open_ticket:{tt['id']}"
            self.add_item(TicketButton(label=label, custom_id=custom_id))


class TicketButton(discord.ui.Button):
    def __init__(self, label: str, custom_id: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            custom_id=custom_id,
        )

    async def callback(self, interaction: discord.Interaction):
        ticket_type_id = int(self.custom_id.split(":")[1])
        await _create_ticket(interaction, ticket_type_id)


# ─────────────────────────────────────────────────────────────────────────────
# Ticket creation
# ─────────────────────────────────────────────────────────────────────────────

async def _create_ticket(interaction: discord.Interaction, ticket_type_id: int):
    """Core ticket creation logic."""
    await interaction.response.defer(ephemeral=True)

    guild  = interaction.guild
    member = interaction.user
    bot    = interaction.client

    # Fetch ticket config from API
    try:
        configs = await bot.api.get_ticket_configs(str(guild.id))
    except Exception as e:
        logger.error(f"Failed to fetch ticket configs: {e}")
        await interaction.followup.send("❌ Could not load ticket configuration.", ephemeral=True)
        return

    config = next((c for c in configs if c["id"] == ticket_type_id), None)
    if not config:
        await interaction.followup.send("❌ Ticket type not found.", ephemeral=True)
        return

    # Resolve category
    category = None
    if config.get("ticket_category_id"):
        category = guild.get_channel(int(config["ticket_category_id"]))

    # Resolve staff role
    staff_role = None
    if config.get("staff_role_id"):
        staff_role = guild.get_role(int(config["staff_role_id"]))

    # Build permission overwrites
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member:             discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=True,
                                read_message_history=True,
                            ),
        guild.me:           discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=True,
                                manage_channels=True,
                            ),
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        )

    # Create the channel (name filled after we get the serial)
    slug = _sanitize_channel_name(config["ticket_name"])
    try:
        channel = await guild.create_text_channel(
            name=f"ticket-{slug}-new",
            category=category,
            overwrites=overwrites,
            reason=f"Ticket opened by {member}",
        )
    except discord.Forbidden:
        await interaction.followup.send("❌ I don't have permission to create channels.", ephemeral=True)
        return

    # Register in API → get serial
    try:
        result = await bot.api.create_ticket(
            server_discord_id=str(guild.id),
            ticket_type_id=ticket_type_id,
            user_discord_id=str(member.id),
            channel_id=str(channel.id),
        )
        serial    = result["serial"]
        ticket_id = result["ticket_id"]
    except Exception as e:
        logger.error(f"Failed to create ticket in API: {e}")
        await channel.delete()
        await interaction.followup.send("❌ Failed to register ticket.", ephemeral=True)
        return

    # Rename with serial
    padded = str(serial).zfill(3)
    await channel.edit(name=f"ticket-{slug}-{padded}")

    # Post welcome embed
    embed = discord.Embed(
        title=f"🎫 {config['ticket_name']}",
        description=config.get("panel_message") or "Thank you for opening a ticket. Staff will be with you shortly.",
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text=f"Ticket #{padded} • Opened by {member.display_name}")

    mention = staff_role.mention if staff_role else ""
    await channel.send(
        content=f"{member.mention} {mention}",
        embed=embed,
        view=TicketControlView(),
    )

    # Log event
    try:
        await bot.api.log_event(
            server_discord_id=str(guild.id),
            event_type="ticket_opened",
            actor_discord_id=str(member.id),
            details={"ticket_id": ticket_id, "serial": serial, "type": config["ticket_name"]},
        )
    except Exception:
        pass  # Non-critical

    await interaction.followup.send(
        f"✅ Ticket created: {channel.mention}", ephemeral=True
    )


async def _close_ticket_channel(interaction: discord.Interaction):
    """Build a transcript, close the ticket, delete the channel."""
    channel = interaction.channel
    guild   = interaction.guild
    bot     = interaction.client

    # Collect transcript
    transcript_lines = []
    async for msg in channel.history(limit=500, oldest_first=True):
        if not msg.author.bot:
            transcript_lines.append(
                f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.author}: {msg.content}"
            )
    transcript = "\n".join(transcript_lines)

    # Notify
    embed = discord.Embed(
        title="🔒 Ticket Closed",
        description=f"Closed by {interaction.user.mention}",
        color=0xED4245,
    )
    await channel.send(embed=embed)

    # Update API
    try:
        await bot.api.log_event(
            server_discord_id=str(guild.id),
            event_type="ticket_closed",
            actor_discord_id=str(interaction.user.id),
            details={"channel": channel.name},
        )
    except Exception:
        pass

    await channel.delete(reason=f"Ticket closed by {interaction.user}")


# ─────────────────────────────────────────────────────────────────────────────
# Slash commands
# ─────────────────────────────────────────────────────────────────────────────

class TicketsCog(commands.Cog, name="Tickets"):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="close", description="Close the current ticket channel.")
    async def close_cmd(self, interaction: discord.Interaction):
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message("This is not a ticket channel.", ephemeral=True)
            return
        staff_role_id = await _get_ticket_staff_role_id(interaction.channel, interaction.client)
        if not await _is_staff(interaction, staff_role_id):
            await interaction.response.send_message("❌ Only staff members can close tickets.", ephemeral=True)
            return
        await interaction.response.send_message(
            "Closing ticket…", view=ConfirmCloseView(), ephemeral=True
        )

    @app_commands.command(name="adduser", description="Add a user to this ticket.")
    @app_commands.describe(member="The member to add")
    async def adduser_cmd(self, interaction: discord.Interaction, member: discord.Member):
        staff_role_id = await _get_ticket_staff_role_id(interaction.channel, interaction.client)
        if not await _is_staff(interaction, staff_role_id):
            await interaction.response.send_message("❌ Only staff members can add users.", ephemeral=True)
            return
        await interaction.channel.set_permissions(member, view_channel=True, send_messages=True)
        await interaction.response.send_message(f"✅ Added {member.mention} to this ticket.")

    @app_commands.command(name="removeuser", description="Remove a user from this ticket.")
    @app_commands.describe(member="The member to remove")
    async def removeuser_cmd(self, interaction: discord.Interaction, member: discord.Member):
        staff_role_id = await _get_ticket_staff_role_id(interaction.channel, interaction.client)
        if not await _is_staff(interaction, staff_role_id):
            await interaction.response.send_message("❌ Only staff members can remove users.", ephemeral=True)
            return
        await interaction.channel.set_permissions(member, view_channel=False)
        await interaction.response.send_message(f"✅ Removed {member.mention} from this ticket.")

    @app_commands.command(name="lock", description="Lock the ticket channel (read-only for the opener).")
    async def lock_cmd(self, interaction: discord.Interaction):
        staff_role_id = await _get_ticket_staff_role_id(interaction.channel, interaction.client)
        if not await _is_staff(interaction, staff_role_id):
            await interaction.response.send_message("❌ Only staff members can lock tickets.", ephemeral=True)
            return
        channel = interaction.channel
        for target, overwrite in channel.overwrites.items():
            if isinstance(target, discord.Member) and target != interaction.guild.me:
                overwrite.send_messages = False
                await channel.set_permissions(target, overwrite=overwrite)
        await interaction.response.send_message("🔒 Ticket locked.")

    @app_commands.command(name="transcript", description="Generate a text transcript of this ticket.")
    async def transcript_cmd(self, interaction: discord.Interaction):
        staff_role_id = await _get_ticket_staff_role_id(interaction.channel, interaction.client)
        if not await _is_staff(interaction, staff_role_id):
            await interaction.response.send_message("❌ Only staff members can generate transcripts.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        channel = interaction.channel
        lines = []
        async for msg in channel.history(limit=500, oldest_first=True):
            lines.append(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.author}: {msg.content}")
        text = "\n".join(lines)
        import io
        file = discord.File(
            fp=io.StringIO(text),
            filename=f"transcript-{channel.name}.txt",
        )
        await interaction.followup.send("📄 Transcript generated:", file=file, ephemeral=True)


async def setup(bot):
    await bot.add_cog(TicketsCog(bot))
    bot.add_view(TicketControlView())
