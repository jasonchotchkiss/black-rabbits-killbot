import discord
from discord import app_commands
from stats import (
    get_year_to_date_top10,
    get_current_month_top10,
    get_current_week_top10,
    format_top10_embed_text,
)


def register_commands(bot):
    """
    Register all slash commands onto the bot's command tree.
    Called once during bot setup.
    """

    @bot.tree.command(
        name="ping",
        description="Check if the bot is alive."
    )
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message(
            "Pong! Black Rabbits Killbot is online."
        )

    @bot.tree.command(
        name="top10",
        description="Show the top 10 Black Rabbits pilots by final blows."
    )
    async def top10(interaction: discord.Interaction):
        # Defer response so Discord doesn't time out while we query the DB
        await interaction.response.defer()

        ytd   = get_year_to_date_top10()
        month = get_current_month_top10()
        week  = get_current_week_top10()

        embed = discord.Embed(
            title="Black Rabbits — Top 10 Final Blows",
            color=discord.Color.red(),
        )

        embed.add_field(
            name="Year to Date",
            value=format_top10_embed_text("YTD", ytd),
            inline=False,
        )
        embed.add_field(
            name="Current Month",
            value=format_top10_embed_text("Month", month),
            inline=False,
        )
        embed.add_field(
            name="Current Week (Mon–Sun)",
            value=format_top10_embed_text("Week", week),
            inline=False,
        )

        embed.set_footer(text="Data sourced from zKillboard • Updates daily at EVE downtime (11:00 UTC)")

        await interaction.followup.send(embed=embed)

    @bot.tree.command(
        name="info",
        description="Learn about the Black Rabbits Killbot and how it works."
    )
    async def info(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Black Rabbits Killbot — Info",
            description="Tracks kill statistics for the Black Rabbits alliance in EVE Online.",
            color=discord.Color.dark_grey(),
        )

        embed.add_field(
            name="What does this bot track?",
            value=(
                "Final blows by Black Rabbits alliance pilots, sourced from "
                "[zKillboard](https://zkillboard.com/alliance/99012611/)."
            ),
            inline=False,
        )

        embed.add_field(
            name="Lists available",
            value=(
                "**Year to Date** — Jan 1 to today (calendar year)\n"
                "**Current Month** — 1st of this month to today\n"
                "**Current Week** — Monday 00:00 UTC to today (resets each Monday)"
            ),
            inline=False,
        )

        embed.add_field(
            name="How often is data updated?",
            value=(
                "Kill data is synced **every 4 hours** (03:00, 07:00, 11:00, 15:00, 19:00, 23:00 UTC), "
                "so `/top10` always reflects recent activity.\\n"
                "A full kill report is posted to this channel daily at **11:15 UTC**, "
                "after EVE Online downtime."
            ),
            inline=False,
        )

        embed.add_field(
            name="Commands",
            value=(
                "`/top10` — Show all three leaderboards\n"
                "`/info` — Show this help message\n"
                "`/ping` — Check if the bot is online"
            ),
            inline=False,
        )

        embed.set_footer(text="Black Rabbits Killbot • Alliance ID: 99012611")

        await interaction.response.send_message(embed=embed)
