# Black Rabbits Killbot

A Discord bot for the **Black Rabbits** alliance in EVE Online that tracks kill statistics and posts leaderboards to your Discord server.

## Features

- Top 10 pilots by final blows: Year to Date, Current Month, Current Week
- Background kill sync every **4 hours** — keeps data fresh around the clock
- Daily automated leaderboard post to `#br-top-killers` at **11:15 UTC** (after EVE downtime)
- Slash commands: `/top10`, `/info`, `/ping`
- Data sourced from zKillboard API + ESI (Alliance ID: 99012611)
- Local SQLite database — no external DB required

## Architecture

| File | Purpose |
|---|---|
| `bot.py` | Discord client, scheduler, daily post logic |
| `commands.py` | Slash command definitions |
| `zkillboard.py` | zKillboard + ESI API fetching and kill extraction |
| `database.py` | SQLite database init, save, and query helpers |
| `stats.py` | Leaderboard queries (YTD, month, week) |
| `sync.py` | Standalone sync script (also called by scheduler) |

## Data Flow

- Every 4 hours: `sync_kills()` fetches from zKillboard + ESI and stores new kills in `killboard.db`
- Daily at 11:15 UTC: bot syncs kills, queries the DB, and posts the leaderboard embed to `#br-top-killers`

## Setup

1. Clone the repo
2. Create a Python virtual environment: `python3 -m venv .venv`
3. Activate it: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env.dev` and fill in your values
6. Run an initial backfill: `python sync.py`
7. Start the bot: `python bot.py`

## Environment Variables

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Your Discord bot token |
| `DISCORD_GUILD_ID` | The Discord server (guild) ID |
| `DISCORD_CHANNEL_ID` | Channel ID for daily automated posts |

## Commands

| Command | Description |
|---|---|
| `/top10` | Shows top 10 pilots by final blows (YTD, Month, Week) |
| `/info` | Bot info, data sources, and update schedule |
| `/ping` | Confirms the bot is online |

## Manual Sync

To pull the latest kills on demand:

    python sync.py

For a deeper historical backfill, run:

    python -c "import asyncio; from sync import sync_kills; asyncio.run(sync_kills(max_pages=20))"

## Notes

- `killboard.db` is gitignored and lives only on the host machine
- Slash commands are synced to the dev guild on startup for instant propagation
- EVE downtime is typically 11:00-11:10 UTC; the daily post fires at 11:15 UTC
