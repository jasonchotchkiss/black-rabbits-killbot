import os

from dotenv import load_dotenv
import discord
from discord import app_commands

# Load environment variables from .env.dev
load_dotenv(".env.dev")

TOKEN      = os.getenv("DISCORD_TOKEN")
GUILD_ID   = os.getenv("DISCORD_GUILD_ID")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

# Validate required env vars are present
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set in .env.dev")
if not GUILD_ID:
    raise RuntimeError("DISCORD_GUILD_ID is not set in .env.dev")
if not CHANNEL_ID:
    raise RuntimeError("DISCORD_CHANNEL_ID is not set in .env.dev")

# Convert IDs to integers (Discord requires integers, not strings)
GUILD_ID   = int(GUILD_ID)
CHANNEL_ID = int(CHANNEL_ID)

# Create a Guild object for faster slash command syncing during dev
DEV_GUILD = discord.Object(id=GUILD_ID)

# Intents are permissions specifying what events the bot receives
intents = discord.Intents.default()

class BlackRabbitsBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync slash commands to dev guild only (instant during development)
        # When we go to prod we will sync globally
        self.tree.copy_global_to(guild=DEV_GUILD)
        await self.tree.sync(guild=DEV_GUILD)

bot = BlackRabbitsBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Watching guild ID : {GUILD_ID}")
    print(f"Posting channel ID: {CHANNEL_ID}")
    print("Bot is ready and slash commands are synced.")

# Simple /ping slash command to confirm everything is working
@bot.tree.command(name="ping", description="Check if the bot is alive.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! Black Rabbits Killbot is online.")

bot.run(TOKEN)