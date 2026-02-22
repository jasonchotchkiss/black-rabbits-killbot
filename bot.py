import os
import asyncio
from datetime import datetime, timezone

from dotenv import load_dotenv
import discord
from discord import app_commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import init_db
from commands import register_commands
from sync import sync_kills, sync_losses
from stats import (
    get_year_to_date_top10,
    get_current_month_top10,
    get_current_week_top10,
    format_top10_embed_text,
)

# ── Environment ────────────────────────────────────────────────────────────────

load_dotenv(".env.dev")

TOKEN      = os.getenv("DISCORD_TOKEN")
GUILD_ID   = os.getenv("DISCORD_GUILD_ID")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set in .env.dev")
if not GUILD_ID:
    raise RuntimeError("DISCORD_GUILD_ID is not set in .env.dev")
if not CHANNEL_ID:
    raise RuntimeError("DISCORD_CHANNEL_ID is not set in .env.dev")

GUILD_ID   = int(GUILD_ID)
CHANNEL_ID = int(CHANNEL_ID)
DEV_GUILD  = discord.Object(id=GUILD_ID)

# ── Bot ────────────────────────────────────────────────────────────────────────

intents = discord.Intents.default()


class BlackRabbitsBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree      = app_commands.CommandTree(self)
        self.scheduler = AsyncIOScheduler(timezone="UTC")

    async def setup_hook(self):
        init_db()
        register_commands(self)
        self.tree.copy_global_to(guild=DEV_GUILD)
        await self.tree.sync(guild=DEV_GUILD)

        # Job 1: Daily kill sync + post to Discord at 11:15 UTC
        self.scheduler.add_job(
            self._daily_post,
            CronTrigger(hour=11, minute=15, timezone="UTC"),
            id="daily_post",
            replace_existing=True,
        )

        # Job 2: Background sync every 4 hours — keeps DB fresh for /top10
        self.scheduler.add_job(
            self._background_sync,
            CronTrigger(hour="3,7,11,15,19,23", minute=0, timezone="UTC"),
            id="background_sync",
            replace_existing=True,
        )

        self.scheduler.start()
        print("Scheduler started — daily post at 11:15 UTC, background sync every 4 hours.")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print(f"Watching guild ID : {GUILD_ID}")
        print(f"Posting channel ID: {CHANNEL_ID}")
        print("Bot is ready and slash commands are synced.")

    async def _daily_post(self):
        """
        Runs every day at 11:15 UTC:
        1. Syncs new kills from zKillboard + ESI into the database
        2. Posts the updated top 10 leaderboard to the configured channel
        """
        print(f"[scheduler] Daily post triggered at {datetime.now(timezone.utc).isoformat()}")

        channel = self.get_channel(CHANNEL_ID)
        if channel is None:
            print(f"[scheduler] ERROR: Could not find channel ID {CHANNEL_ID}. Aborting.")
            return

        try:
            await sync_kills(max_pages=5)
            await sync_losses(max_pages=5)
            print("[scheduler] Kill sync complete.")
        except Exception as e:
            print(f"[scheduler] Kill sync failed: {e}")
            await channel.send(f"⚠️ Daily kill sync encountered an error: `{e}`")
            return

        now       = datetime.now(timezone.utc)
        month     = now.strftime("%B %Y")
        week_start = _get_monday_label(now)

        ytd       = get_year_to_date_top10()
        month_top = get_current_month_top10()
        week      = get_current_week_top10()

        embed = discord.Embed(
            title       = "⚔️  Black Rabbits — Daily Kill Report",
            description = f"Updated <t:{int(now.timestamp())}:F>",
            color       = discord.Color.red(),
        )
        embed.add_field(
            name   = f"📅 Year to Date ({now.year})",
            value  = format_top10_embed_text("YTD", ytd),
            inline = False,
        )
        embed.add_field(
            name   = f"🗓️ Current Month ({month})",
            value  = format_top10_embed_text("Month", month_top),
            inline = False,
        )
        embed.add_field(
            name   = f"📆 Current Week ({week_start})",
            value  = format_top10_embed_text("Week", week),
            inline = False,
        )
        embed.set_footer(text="Data: zKillboard + ESI  •  Updates daily at 11:15 UTC after EVE downtime")

        await channel.send(embed=embed)
        print(f"[scheduler] Daily post sent to channel {CHANNEL_ID}.")

    async def _background_sync(self):
        """
        Runs every 4 hours — silently syncs new kills into the DB.
        No Discord post. Keeps /top10 results fresh between daily posts.
        """
        print(f"[scheduler] Background sync started at {datetime.now(timezone.utc).isoformat()}")
        try:
            await sync_kills(max_pages=3)
            await sync_losses(max_pages=3)
            print("[scheduler] Background sync complete.")
        except Exception as e:
            print(f"[scheduler] Background sync failed: {e}")


def _get_monday_label(now: datetime) -> str:
    """Returns a 'D Mon' label for the start of the current week."""
    from datetime import timedelta
    days_since_monday = now.weekday()
    monday = now - timedelta(days=days_since_monday)
    return monday.strftime("%-d %b")


bot = BlackRabbitsBot()
bot.run(TOKEN)
