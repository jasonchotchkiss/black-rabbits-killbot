import os

from dotenv import load_dotenv
import discord
from discord import app_commands

from database import init_db
from commands import register_commands

# Load environment variables from .env.dev
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

intents = discord.Intents.default()


class BlackRabbitsBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Initialize database on startup
        init_db()

        # Register all slash commands
        register_commands(self)

        # Sync commands to dev guild
        self.tree.copy_global_to(guild=DEV_GUILD)
        await self.tree.sync(guild=DEV_GUILD)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print(f"Watching guild ID : {GUILD_ID}")
        print(f"Posting channel ID: {CHANNEL_ID}")
        print("Bot is ready and slash commands are synced.")


bot = BlackRabbitsBot()
bot.run(TOKEN)
