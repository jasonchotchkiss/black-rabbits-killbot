import discord
from discord import app_commands
from stats import (
    get_year_to_date_top10,
    get_current_month_top10,
    get_current_week_top10,
    get_year_to_date_top10_solo,
    get_current_month_top10_solo,
    get_current_week_top10_solo,
    get_year_to_date_top10_solo_deaths,
    get_current_month_top10_solo_deaths,
    get_current_week_top10_solo_deaths,
    get_top10_solo_kd,
    format_top10_embed_text,
    get_kills_against_character,
    get_kills_against_corp,
    get_kills_against_alliance,
    get_top_damage_dealers,
    search_character_victims,
    search_corporations,
    search_alliances,
    get_top10_all_kills,
)
from database import get_corporation_name, get_alliance_name

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
        await interaction.response.defer()

        ytd   = get_year_to_date_top10()
        month = get_current_month_top10()
        week  = get_current_week_top10()

        embed = discord.Embed(
            title="Black Rabbits \u2014 Top 10 Final Blows",
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
            name="Current Week (Mon\u2013Sun)",
            value=format_top10_embed_text("Week", week),
            inline=False,
        )

        embed.set_footer(text="Data sourced from zKillboard \u2022 Updates daily at EVE downtime (11:00 UTC)")

        await interaction.followup.send(embed=embed)

    @bot.tree.command(
          name="top10solo",
          description="Show the top 10 Black Rabbits pilots by solo final blows."
      )
    async def top10solo(interaction: discord.Interaction):
          await interaction.response.defer()

          ytd   = get_year_to_date_top10_solo()
          month = get_current_month_top10_solo()
          week  = get_current_week_top10_solo()

          embed = discord.Embed(
              title="Black Rabbits \u2014 Top 10 Solo Kills",
              color=discord.Color.red(),
          )

          embed.add_field(
              name="Year to Date",
              value=format_top10_embed_text("YTD", ytd, label="solo kill"),
              inline=False,
          )
          embed.add_field(
              name="Current Month",
              value=format_top10_embed_text("Month", month, label="solo kill"),
              inline=False,
          )
          embed.add_field(
              name="Current Week (Mon\u2013Sun)",
              value=format_top10_embed_text("Week", week, label="solo kill"),
              inline=False,
          )

          embed.set_footer(text="Data sourced from zKillboard \u2022 Updates daily at EVE downtime (11:00 UTC)")

          await interaction.followup.send(embed=embed)

    @bot.tree.command(
          name="topdamage",
          description="Show the top 10 Black Rabbits pilots by total damage dealt."
      )
    async def topdamage(interaction: discord.Interaction):
          await interaction.response.defer()

          ytd   = get_top_damage_dealers("ytd")
          month = get_top_damage_dealers("month")
          week  = get_top_damage_dealers("week")

          embed = discord.Embed(
              title="Black Rabbits \u2014 Top 10 Damage Dealers",
              color=discord.Color.red(),
          )

          def format_damage_text(results):
              if not results:
                  return "No damage recorded for this period."
              medals = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}
              lines = []
              for entry in results:
                  medal = medals.get(entry["rank"], f"`#{entry['rank']}`")
                  lines.append(
                      f"{medal} **{entry['pilot_name']}** \u2014 {entry['damage']:,} damage"
                  )
              return "\n".join(lines)

          embed.add_field(
              name="Year to Date",
              value=format_damage_text(ytd),
              inline=False,
          )
          embed.add_field(
              name="Current Month",
              value=format_damage_text(month),
              inline=False,
          )
          embed.add_field(
              name="Current Week (Mon\u2013Sun)",
              value=format_damage_text(week),
              inline=False,
          )

          embed.set_footer(text="Data sourced from zKillboard \u2022 Updates daily at EVE downtime (11:00 UTC)")

          await interaction.followup.send(embed=embed)

    @bot.tree.command(
        name="info",
        description="Learn about the Black Rabbits Killbot and how it works."
    )
    async def info(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Black Rabbits Killbot \u2014 Info",
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
                "**Year to Date** \u2014 Jan 1 to today (calendar year)\n"
                "**Current Month** \u2014 1st of this month to today\n"
                "**Current Week** \u2014 Monday 00:00 UTC to today (resets each Monday)"
            ),
            inline=False,
        )

        embed.add_field(
            name="How often is data updated?",
            value=(
                "Kill data is synced **every 4 hours** (03:00, 07:00, 11:00, 15:00, 19:00, 23:00 UTC), "
                "so `/top10` always reflects recent activity.\n"
                "A full kill report is posted to this channel daily at **11:15 UTC**, "
                "after EVE Online downtime."
            ),
            inline=False,
        )

        embed.add_field(
            name="Commands",
            value=(
                "`/top10` \u2014 Show all three leaderboards\n"
                "`/top10solo` \u2014 Show top 10 solo kill leaderboards\n"
                "`/top10solodeaths` \u2014 Show top 10 solo death leaderboards\n"
                "`/top10solokd` \u2014 Show top 10 solo K/D ratio leaderboards\n"
                "`/topdamage` \u2014 Show top 10 pilots by total damage dealt\n"
                "`/top10allkills` \u2014 Show top 10 pilots by total kill participation\n"
                "`/mystats <pilot>` \u2014 Your personal kill stats card (only you can see it)\n"
                "`/killsagainst <target>` \u2014 Top 10 BR pilots who killed a specific pilot, corp, or alliance\n"
                "`/info` \u2014 Show this help message\n"
                "`/ping` \u2014 Check if the bot is online"
            ),

            inline=False,
        )

        embed.set_footer(text="Black Rabbits Killbot \u2022 Alliance ID: 99012611")

        await interaction.response.send_message(embed=embed)

    async def target_autocomplete(
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        choices = []

        # Characters — encoded as "char:Name"
        for r in search_character_victims(current):
            label = f"Pilot: {r['name']} ({r['count']} kills)"
            value = f"char:{r['name']}"
            choices.append(app_commands.Choice(name=label[:100], value=value[:100]))

        # Corporations — encoded as "corp:ID"
        for r in search_corporations(current):
            label = f"Corp: {r['name']} [{r['ticker']}]"
            value = f"corp:{r['id']}"
            choices.append(app_commands.Choice(name=label[:100], value=value[:100]))

        # Alliances — encoded as "ally:ID"
        for r in search_alliances(current):
            label = f"Alliance: {r['name']} [{r['ticker']}]"
            value = f"ally:{r['id']}"
            choices.append(app_commands.Choice(name=label[:100], value=value[:100]))

        return choices[:25]

    @bot.tree.command(
        name="killsagainst",
        description="Pilot name (autocomplete), or type an exact corp/alliance name."
    )
    @app_commands.describe(target="Start typing a pilot, corp, or alliance name")
    @app_commands.autocomplete(target=target_autocomplete)
    async def killsagainst(interaction: discord.Interaction, target: str):
        await interaction.response.defer()

        if target.startswith("char:"):
              name = target[5:]
              results = get_kills_against_character(name)
              entity_label = f"**{name}**"

        elif target.startswith("corp:"):
              corp_id = int(target[5:])
              results = get_kills_against_corp(corp_id)
              corp_name = get_corporation_name(corp_id) or str(corp_id)
              entity_label = f"**{corp_name}** (corporation)"

        elif target.startswith("ally:"):
              alliance_id = int(target[5:])
              results = get_kills_against_alliance(alliance_id)
              alliance_name = get_alliance_name(alliance_id) or str(alliance_id)
              entity_label = f"**{alliance_name}** (alliance)"

        else:
              # Free-text fallback — fuzzy character name search
              results = get_kills_against_character(target)
              entity_label = f'pilot matching "{target}"'

        embed = discord.Embed(
              title=f"Kills Against \u2014 {entity_label} (all time)",
              color=discord.Color.red(),
          )

        if not results:
            embed.description = f"No kills found against {entity_label}."
        else:
            medals = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}
            lines = []
            for entry in results:
                rank  = entry["rank"]
                name  = entry["pilot_name"]
                kills = entry["kills"]
                medal = medals.get(rank, f"`#{rank}`")
                lines.append(f"{medal} **{name}** \u2014 {kills} kill{'s' if kills != 1 else ''}")

            embed.add_field(
                name=f"Top BR Pilots vs {entity_label}",
                value="\n".join(lines),
                inline=False,
         )

        embed.set_footer(text="Data sourced from zKillboard")

        await interaction.followup.send(embed=embed)


    @bot.tree.command(
          name="top10solodeaths",
          description="Show the top 10 Black Rabbits pilots by solo deaths."
      )
    async def top10solodeaths(interaction: discord.Interaction):
          await interaction.response.defer()

          ytd   = get_year_to_date_top10_solo_deaths()
          month = get_current_month_top10_solo_deaths()
          week  = get_current_week_top10_solo_deaths()

          embed = discord.Embed(
              title="Black Rabbits \u2014 Top 10 Solo Deaths",
              color=discord.Color.red(),
          )

          embed.add_field(
              name="Year to Date",
              value=format_top10_embed_text("YTD", ytd, label="death"),
              inline=False,
          )
          embed.add_field(
              name="Current Month",
              value=format_top10_embed_text("Month", month, label="death"),
              inline=False,
          )
          embed.add_field(
              name="Current Week (Mon\u2013Sun)",
              value=format_top10_embed_text("Week", week, label="death"),
              inline=False,
          )

          embed.set_footer(text="Data sourced from zKillboard \u2022 Updates daily at EVE downtime (11:00 UTC)")

          await interaction.followup.send(embed=embed)

    @bot.tree.command(
          name="top10solokd",
          description="Show the top 10 Black Rabbits pilots by solo K/D ratio."
      )
    async def top10solokd(interaction: discord.Interaction):
          await interaction.response.defer()

          ytd   = get_top10_solo_kd("ytd")
          month = get_top10_solo_kd("month")
          week  = get_top10_solo_kd("week")

          embed = discord.Embed(
              title="Black Rabbits \u2014 Top 10 Solo K/D Ratio",
              color=discord.Color.red(),
          )

          def format_kd_text(results):
              if not results:
                  return "No data recorded for this period."
              medals = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}
              lines = []
              for entry in results:
                  medal = medals.get(entry["rank"], f"`#{entry['rank']}`")
                  lines.append(
                  f"{medal} **{entry['pilot_name']}** \u2014 "
                  f"{entry['kills']}/{entry['deaths']} K:D  `{entry['kd']:.2f}`"
                  )
              return "\n".join(lines)

          embed.add_field(
              name="Year to Date",
              value=format_kd_text(ytd),
              inline=False,
          )
          embed.add_field(
              name="Current Month",
              value=format_kd_text(month),
              inline=False,
          )
          embed.add_field(
              name="Current Week (Mon\u2013Sun)",
              value=format_kd_text(week),
              inline=False,
          )

          embed.set_footer(text="Data sourced from zKillboard \u2022 Updates daily at EVE downtime (11:00 UTC)")

          await interaction.followup.send(embed=embed)

    @bot.tree.command(
            name="top10allkills",
            description="Show the top 10 Black Rabbits pilots by total kill participation."
        )
    async def top10allkills(interaction: discord.Interaction):
            await interaction.response.defer()

            ytd   = get_top10_all_kills("ytd")
            month = get_top10_all_kills("month")
            week  = get_top10_all_kills("week")

            embed = discord.Embed(
                title="Black Rabbits \u2014 Top 10 Kill Participation",
                color=discord.Color.red(),
            )

            embed.add_field(
                name="Year to Date",
                value=format_top10_embed_text("YTD", ytd, label="kill"),
                inline=False,
            )
            embed.add_field(
                name="Current Month",
                value=format_top10_embed_text("Month", month, label="kill"),
                inline=False,
            )
            embed.add_field(
                name="Current Week (Mon\u2013Sun)",
                value=format_top10_embed_text("Week", week, label="kill"),
                inline=False,
            )

            embed.set_footer(text="Data sourced from zKillboard \u2022 Updates daily at EVE downtime (11:00 UTC)")

            await interaction.followup.send(embed=embed)

    async def pilot_autocomplete(
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        choices = []
        for r in search_all_pilots(current):
            label = f"{r['name']} ({r['count']} kills)"
            value = f"{r['char_id']}:{r['name']}"
            choices.append(app_commands.Choice(name=label[:100], value=value[:100]))
        return choices[:25]

    @bot.tree.command(
        name="mystats",
        description="See your personal kill stats. Only you can see the result."
    )
    @app_commands.describe(pilot="Start typing your pilot name")
    @app_commands.autocomplete(pilot=pilot_autocomplete)
    async def mystats(interaction: discord.Interaction, pilot: str):
        await interaction.response.defer(ephemeral=True)

        if ":" in pilot:
            char_id_str, char_name = pilot.split(":", 1)
            try:
                char_id = int(char_id_str)
            except ValueError:
                await interaction.followup.send(
                    "Could not parse pilot. Please select from the autocomplete list.",
                    ephemeral=True
                )
                return
        else:
            await interaction.followup.send(
                "Please select a pilot from the autocomplete list.",
                ephemeral=True
            )
            return

        ytd   = get_pilot_stats(char_name, char_id, "ytd")
        month = get_pilot_stats(char_name, char_id, "month")
        week  = get_pilot_stats(char_name, char_id, "week")

        def format_stats(s: dict) -> str:
            return (
                f"Kill Participation: **{s['kill_participation']}**\n"
                f"Final Blows: **{s['final_blows']}**\n"
                f"Solo Kills: **{s['solo_kills']}**\n"
                f"Solo Losses: **{s['solo_losses']}**"
            )

        embed = discord.Embed(
            title=f"\U0001f4ca {char_name} \u2014 Personal Stats",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="Year to Date",
            value=format_stats(ytd),
            inline=False,
        )
        embed.add_field(
            name="Current Month",
            value=format_stats(month),
            inline=False,
        )
        embed.add_field(
            name="Current Week (Mon\u2013Sun)",
            value=format_stats(week),
            inline=False,
        )

        embed.set_footer(text="Only visible to you \u2022 Data sourced from zKillboard")

        await interaction.followup.send(embed=embed, ephemeral=True)

        
