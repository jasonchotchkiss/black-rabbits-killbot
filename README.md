# Black Rabbits Killbot

A Discord bot for the Black Rabbits alliance (Eve Online).

## Features
- Top 10 pilots by final blows: Year to Date, Current Month, Current Week
- Daily automated posting to `#br-top-killers` channel aligned to EVE downtime
- Slash commands: `/top10`, `/info`, `/ping`
- Data sourced from zKillboard API (Alliance ID: 99012611)

## Setup

1. Clone the repo
2. Create a Python virtual environment: `python3 -m venv .venv`
3. Activate it: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env.dev` and fill in your values
6. Run: `python bot.py`

## Environment Variables

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Bot token from Discord Developer Portal |
| `DISCORD_GUILD_ID` | Discord server ID |
| `DISCORD_CHANNEL_ID` | Channel ID for `#br-top-killers` |

## Deployment

Managed by systemd. See deployment notes for production setup.
