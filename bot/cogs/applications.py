"""
Applications cog.
Handles application button interactions, Q&A flow, and staff commands.

Fixes applied vs. original:
  - ReviewView custom_id embeds application_id (unique per review, works after restart)
  - _finish_application receives bot explicitly (no private _state._get_client() hack)
  - Staff role check on /approve and /reject commands
  - Answer length validation (max 2000 chars per answer)
  - In-memory sessions include an `expires_at` field and a background cleanup task
"""

import asyncio
import logging
import re
import time
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

logger = logging.getLogger(__name__)

# ── Session store ─────────────────────────────────────────────────────────────
# {channel_id: {session data}}
# Sessions expire after 2 hours of inactivity to prevent orphaned channels.
_active_sessions: dict = {}
SESSION_TIMEOUT_SECONDS = 7200  # 2 hours

MAX_ANSWER_LENGTH = 2000  # characters per answer


def _sanitize_channel_name(text: str) -> str:
    return re.sub(r"[^a-z0-9-]", "", text.lower().replace(" ", "-"))[:32]


async def _is_app_staff(interaction: discord.Interaction, staff_role_id: str | None = None) -> bool:
    if interaction.user.guild_permissions.administrator:
        return True
    if staff_role_id:
        role = interaction.guild.get_role(int(staff_role_id))
        if role and role in interaction.user.roles:
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────────────────────────────────────

class ApplicationOpenView(discord.ui.View):
    """Buttons for opening an application type. custom_id = open_app:{type_id}"""

    def __init__(self, app_types: list):
        super().__init__(timeout=None)
        for at in app_types:
            label     = at.get("button_label") or at["application_name"]
            custom_id = f"open_app:{at['id']}"
            self.add_item(ApplicationButton(label=label, custom_id=custom_id))


class ApplicationButton(discord.ui.Button):
    def __init__(self, label: str, custom_id: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.success,
            custom_id=custom_id,
        )

    async def callback(self, interaction: discord.Interaction):
        app_type_id = int(self.custom_id.split(":")[1])
        await _start_application(interaction, app_type_id)


class ReviewView(discord.ui.View):
    """
    Approve / Reject buttons for staff.
    application_id is embedded in custom_id so it survives bot restarts.
    """

    def __init__(self, application_id: int, staff_role_id: str | None = None):
        super().__init__(timeout=None)
        self.application_id = application_id
        self.staff_role_id  = staff_role_id
        # Unique custom_ids per application — works after restart
        self.add_item(ReviewButton(
            label="✅ Approve",
            style=discord.ButtonStyle.success,
            custom_id=f"app_approve:{application_id}",
        ))
        self.add_item(ReviewButton(
            label="❌ Reject",
            style=discord.ButtonStyle.danger,
            custom_id=f"app_reject:{application_id}",
        ))


class ReviewButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        parts     = self.custom_id.split(":")
        action    = parts[0]          # "app_approve" or "app_reject"
        app_id    = int(parts[1])
        status    = "approved" if action == "app_approve" else "rejected"

        # Fetch config to get staff_role_id for this application's guild
        bot = interaction.client
        try:
            configs = await bot.api.get_application_configs(str(interaction.guild.id))
        except Exception:
            configs = []

        staff_role_id = None
        for c in configs:
            if c.get("staff_role_id"):
                staff_role_id = c["staff_role_id"]
                break

        if not await _is_app_staff(interaction, staff_role_id):
            await interaction.response.send_message(
                "❌ Only staff members can review applications.", ephemeral=True
            )
            return

        await _review_application(interaction, app_id, status)


# ─────────────────────────────────────────────────────────────────────────────
# Application flow
# ─────────────────────────────────────────────────────────────────────────────

async def _start_application(interaction: discord.Interaction, app_type_id: int):
    """Create application channel and start the Q&A flow."""
    await interaction.response.defer(ephemeral=True)

    guild  = interaction.guild
    member = interaction.user
    bot    = interaction.client

    try:
        configs = await bot.api.get_application_configs(str(guild.id))
    except Exception as e:
        logger.error(f"Failed to fetch application configs: {e}")
        await interaction.followup.send("❌ Could not load application configuration.", ephemeral=True)
        return

    config = next((c for c in configs if c["id"] == app_type_id), None)
    if not config:
        await interaction.followup.send("❌ Application type not found.", ephemeral=True)
        return

    if not config.get("questions"):
        await interaction.followup.send("❌ This application has no questions configured.", ephemeral=True)
        return

    category   = guild.get_channel(int(config["category_id"])) if config.get("category_id") else None
    staff_role = guild.get_role(int(config["staff_role_id"])) if config.get("staff_role_id") else None

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member:             discord.PermissionOverwrite(
                                view_channel=True, send_messages=True, read_message_history=True,
                            ),
        guild.me:           discord.PermissionOverwrite(
                                view_channel=True, send_messages=True, manage_channels=True,
                            ),
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    safe_name = _sanitize_channel_name(config["application_name"])
    safe_user = _sanitize_channel_name(member.name)
    try:
        channel = await guild.create_text_channel(
            name=f"application-{safe_name}-{safe_user}"[:100],
            category=category,
            overwrites=overwrites,
            reason=f"Application opened by {member}",
        )
    except discord.Forbidden:
        await interaction.followup.send("❌ I don't have permission to create channels.", ephemeral=True)
        return

    _active_sessions[channel.id] = {
        "app_type":       config,
        "app_type_id":    app_type_id,
        "user":           member,
        "answers":        {},
        "question_index": 0,
        "guild_id":       str(guild.id),
        "expires_at":     time.monotonic() + SESSION_TIMEOUT_SECONDS,
    }

    embed = discord.Embed(
        title=f"📋 {config['application_name']}",
        description=config.get("welcome_message") or "Please answer the following questions honestly.",
        color=0x57F287,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text=f"Application • {member.display_name}")
    await channel.send(content=member.mention, embed=embed)
    await _ask_next_question(channel, _active_sessions[channel.id], bot)

    await interaction.followup.send(f"✅ Application started: {channel.mention}", ephemeral=True)


async def _ask_next_question(channel: discord.TextChannel, session: dict, bot):
    """Send the next question embed."""
    questions = session["app_type"]["questions"]
    idx       = session["question_index"]

    if idx >= len(questions):
        await _finish_application(channel, session, bot)
        return

    q = questions[idx]
    embed = discord.Embed(
        description=f"**Question {idx + 1} of {len(questions)}**\n\n{q['question_text']}",
        color=0x5865F2,
    )
    await channel.send(embed=embed)


async def _finish_application(channel: discord.TextChannel, session: dict, bot):
    """All questions answered – save to API and notify."""
    try:
        result = await bot.api.create_application(
            server_discord_id=session["guild_id"],
            application_type_id=session["app_type_id"],
            user_discord_id=str(session["user"].id),
            channel_id=str(channel.id),
            answers=session["answers"],
        )
    except Exception as e:
        logger.error(f"Failed to save application: {e}")
        await channel.send("❌ Failed to save your application. Please contact an admin.")
        return

    embed = discord.Embed(
        title="✅ Application Complete",
        description=session["app_type"].get("completion_message") or
                    "Thank you for completing the application. Leadership will review your submission.",
        color=0x57F287,
    )
    await channel.send(embed=embed)

    summary_lines = []
    for q in session["app_type"]["questions"]:
        answer = session["answers"].get(str(q["id"]), "*No answer*")
        summary_lines.append(f"**{q['question_text']}**\n{answer}")

    application_id = result.get("application_id")
    staff_role     = None
    staff_role_id  = session["app_type"].get("staff_role_id")
    if staff_role_id:
        staff_role = channel.guild.get_role(int(staff_role_id))

    summary_embed = discord.Embed(
        title=f"📋 Application Summary – {session['user'].display_name}",
        description="\n\n".join(summary_lines),
        color=0xFEE75C,
    )
    summary_embed.add_field(name="Application ID", value=str(application_id or "?"))

    await channel.send(
        content=staff_role.mention if staff_role else "",
        embed=summary_embed,
        view=ReviewView(application_id, staff_role_id),
    )

    try:
        await bot.api.log_event(
            server_discord_id=session["guild_id"],
            event_type="application_submitted",
            actor_discord_id=str(session["user"].id),
            details={"application_id": application_id},
        )
    except Exception:
        pass

    _active_sessions.pop(channel.id, None)


async def _review_application(interaction: discord.Interaction, app_id: int, status: str):
    await interaction.response.defer()
    bot = interaction.client
    try:
        await bot.api.review_application(
            application_id=app_id,
            status=status,
            reviewer_discord_id=str(interaction.user.id),
        )
    except Exception as e:
        logger.error(f"Failed to review application {app_id}: {e}")

    color = 0x57F287 if status == "approved" else 0xED4245
    label = "Approved ✅" if status == "approved" else "Rejected ❌"
    embed = discord.Embed(
        description=f"Application **{label}** by {interaction.user.mention}",
        color=color,
    )
    await interaction.followup.send(embed=embed)

    try:
        await bot.api.log_event(
            server_discord_id=str(interaction.guild.id),
            event_type=f"application_{status}",
            actor_discord_id=str(interaction.user.id),
            details={"application_id": app_id},
        )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Cog
# ─────────────────────────────────────────────────────────────────────────────

class ApplicationsCog(commands.Cog, name="Applications"):

    def __init__(self, bot):
        self.bot = bot
        self._session_cleanup.start()

    def cog_unload(self):
        self._session_cleanup.cancel()

    @tasks.loop(minutes=15)
    async def _session_cleanup(self):
        """Remove expired application sessions and delete orphaned channels."""
        now = time.monotonic()
        expired = [cid for cid, s in _active_sessions.items() if s["expires_at"] < now]
        for channel_id in expired:
            session = _active_sessions.pop(channel_id, None)
            if not session:
                continue
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(
                        "⏰ This application timed out due to inactivity and will be deleted shortly."
                    )
                    await asyncio.sleep(5)
                    await channel.delete(reason="Application session timed out")
                except Exception:
                    pass
            logger.info(f"Cleaned up expired application session for channel {channel_id}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Intercept messages in active application channels to collect answers."""
        if message.author.bot:
            return
        session = _active_sessions.get(message.channel.id)
        if not session:
            return
        if message.author.id != session["user"].id:
            return

        questions = session["app_type"]["questions"]
        idx       = session["question_index"]
        if idx >= len(questions):
            return

        # Enforce answer length limit
        answer = message.content[:MAX_ANSWER_LENGTH]

        q_id = str(questions[idx]["id"])
        session["answers"][q_id]  = answer
        session["question_index"] += 1
        session["expires_at"]     = time.monotonic() + SESSION_TIMEOUT_SECONDS  # refresh timeout

        await _ask_next_question(message.channel, session, self.bot)

    @app_commands.command(name="approve", description="Approve an application by ID.")
    @app_commands.describe(application_id="The numeric application ID")
    async def approve_cmd(self, interaction: discord.Interaction, application_id: int):
        # Fetch staff_role_id for this guild
        try:
            configs = await self.bot.api.get_application_configs(str(interaction.guild.id))
        except Exception:
            configs = []
        staff_role_id = next((c.get("staff_role_id") for c in configs if c.get("staff_role_id")), None)

        if not await _is_app_staff(interaction, staff_role_id):
            await interaction.response.send_message("❌ Only staff members can approve applications.", ephemeral=True)
            return
        await interaction.response.defer()
        await _review_application(interaction, application_id, "approved")

    @app_commands.command(name="reject", description="Reject an application by ID.")
    @app_commands.describe(application_id="The numeric application ID")
    async def reject_cmd(self, interaction: discord.Interaction, application_id: int):
        try:
            configs = await self.bot.api.get_application_configs(str(interaction.guild.id))
        except Exception:
            configs = []
        staff_role_id = next((c.get("staff_role_id") for c in configs if c.get("staff_role_id")), None)

        if not await _is_app_staff(interaction, staff_role_id):
            await interaction.response.send_message("❌ Only staff members can reject applications.", ephemeral=True)
            return
        await interaction.response.defer()
        await _review_application(interaction, application_id, "rejected")


async def setup(bot):
    await bot.add_cog(ApplicationsCog(bot))
