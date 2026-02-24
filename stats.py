import sqlite3
from datetime import datetime, timezone, timedelta
from database import get_connection


def get_year_to_date_top10() -> list[dict]:
    """
    Returns the top 10 pilots by final blow count
    for the current calendar year (Jan 1 to now UTC).
    """
    now = datetime.now(timezone.utc)
    start = datetime(now.year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    return _query_top10(start.isoformat(), now.isoformat())


def get_current_month_top10() -> list[dict]:
    """
    Returns the top 10 pilots by final blow count
    for the current calendar month (1st to now UTC).
    """
    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)

    return _query_top10(start.isoformat(), now.isoformat())


def get_current_week_top10() -> list[dict]:
    """
    Returns the top 10 pilots by final blow count
    for the current week (Monday 00:00 UTC to now UTC).
    Week runs Monday to Sunday.
    """
    now = datetime.now(timezone.utc)
    # weekday() returns 0 for Monday, 6 for Sunday
    days_since_monday = now.weekday()
    monday = now - timedelta(days=days_since_monday)
    start = monday.replace(hour=0, minute=0, second=0, microsecond=0)

    return _query_top10(start.isoformat(), now.isoformat())


def _query_top10(start_iso: str, end_iso: str, is_solo: bool = False) -> list[dict]:
    """
    Internal helper: queries the database for top 10 pilots
    by final blow count between start_iso and end_iso timestamps.

    Returns a list of dicts with rank, pilot name, and kill count.
    """
    conn = get_connection()
    cursor = conn.cursor()

    solo_filter = "AND is_solo = 1" if is_solo else ""
    unknown_filter = "AND final_blow_name != 'Unknown Pilot'" if is_solo else ""

    cursor.execute(f"""
        SELECT
            final_blow_name,
            final_blow_id,
            COUNT(*) as kill_count
        FROM kills
        WHERE kill_time >= ?
          AND kill_time <= ?
         AND final_blow_id != 0
           {solo_filter}
           {unknown_filter}
        GROUP BY final_blow_id, final_blow_name
        ORDER BY kill_count DESC
        LIMIT 10
    """, (start_iso, end_iso))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for rank, (name, char_id, count) in enumerate(rows, start=1):
        results.append({
            "rank":       rank,
            "pilot_name": name,
            "char_id":    char_id,
            "kills":      count,
            "zkb_url":    f"https://zkillboard.com/character/{char_id}/",
        })

    return results

def get_top_damage_dealers(period: str = "ytd") -> list[dict]:
    """
    Returns top 10 pilots by total damage done across all kills
    for the given period: 'ytd', 'month', or 'week'.
    """
    now = datetime.now(timezone.utc)

    if period == "ytd":
        start = datetime(now.year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    elif period == "month":
        start = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
    elif period == "week":
        days_since_monday = now.weekday()
        monday = now - timedelta(days=days_since_monday)
        start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Unknown period: {period}")

    return _query_top_damage(start.isoformat(), now.isoformat())


def _query_top_damage(start_iso: str, end_iso: str) -> list[dict]:
    """
    Internal helper: queries the attackers table for top 10 pilots
    by total damage done between start_iso and end_iso timestamps.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            character_name,
            character_id,
            SUM(damage_done) as total_damage
        FROM attackers
        WHERE kill_timestamp >= ?
          AND kill_timestamp <= ?
          AND character_id != 0
        GROUP BY character_id, character_name
        ORDER BY total_damage DESC
        LIMIT 10
    """, (start_iso, end_iso))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for rank, (name, char_id, damage) in enumerate(rows, start=1):
        results.append({
            "rank":       rank,
            "pilot_name": name,
            "char_id":    char_id,
            "damage":     damage,
            "zkb_url":    f"https://zkillboard.com/character/{char_id}/",
        })

    return results

def get_year_to_date_top10_solo() -> list[dict]:
    """Returns top 10 pilots by solo final blow count for the current calendar year."""
    now = datetime.now(timezone.utc)
    start = datetime(now.year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    return _query_top10(start.isoformat(), now.isoformat(), is_solo=True)


def get_current_month_top10_solo() -> list[dict]:
    """Returns top 10 pilots by solo final blow count for the current calendar month."""
    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
    return _query_top10(start.isoformat(), now.isoformat(), is_solo=True)


def get_current_week_top10_solo() -> list[dict]:
    """Returns top 10 pilots by solo final blow count for the current week (Mon–Sun UTC)."""
    now = datetime.now(timezone.utc)
    days_since_monday = now.weekday()
    monday = now - timedelta(days=days_since_monday)
    start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return _query_top10(start.isoformat(), now.isoformat(), is_solo=True) 

def _query_top10_deaths(start_iso: str, end_iso: str) -> list[dict]:
    """
    Internal helper: queries the database for top 10 pilots
    by solo death count (is_loss=1, is_solo=1) between start_iso and end_iso.
    Uses victim_name as the pilot identifier.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            victim_name,
            COUNT(*) as death_count
        FROM kills
        WHERE kill_time >= ?
          AND kill_time <= ?
          AND is_loss = 1
          AND is_solo = 1
          AND victim_name IS NOT NULL
          AND victim_name != ''
        GROUP BY victim_name
        ORDER BY death_count DESC
        LIMIT 10
    """, (start_iso, end_iso))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for rank, (name, count) in enumerate(rows, start=1):
        results.append({
            "rank":       rank,
            "pilot_name": name,
            "kills":      count,
        })

    return results

def get_year_to_date_top10_solo_deaths() -> list[dict]:
    """Returns top 10 pilots by solo death count for the current calendar year."""
    now = datetime.now(timezone.utc)
    start = datetime(now.year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    return _query_top10_deaths(start.isoformat(), now.isoformat())


def get_current_month_top10_solo_deaths() -> list[dict]:
    """Returns top 10 pilots by solo death count for the current calendar month."""
    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
    return _query_top10_deaths(start.isoformat(), now.isoformat())


def get_current_week_top10_solo_deaths() -> list[dict]:
    """Returns top 10 pilots by solo death count for the current week (Mon–Sun UTC)."""
    now = datetime.now(timezone.utc)
    days_since_monday = now.weekday()
    monday = now - timedelta(days=days_since_monday)
    start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return _query_top10_deaths(start.isoformat(), now.isoformat())


def get_top10_solo_kd(period: str = "ytd") -> list[dict]:
    """
    Returns top 10 pilots by solo K/D ratio for the given period.
    KD = solo_kills / max(solo_deaths, 1)
    Only includes pilots who appear in either the solo kills or solo deaths list.
    """
    now = datetime.now(timezone.utc)

    if period == "ytd":
        start = datetime(now.year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    elif period == "month":
        start = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
    elif period == "week":
        days_since_monday = now.weekday()
        monday = now - timedelta(days=days_since_monday)
        start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Unknown period: {period}")

    start_iso = start.isoformat()
    end_iso   = now.isoformat()

    kills_list  = _query_top10(start_iso, end_iso, is_solo=True)
    deaths_list = _query_top10_deaths(start_iso, end_iso)

    # Build dicts keyed by pilot name
    kills_by_name  = {e["pilot_name"]: e["kills"] for e in kills_list}
    deaths_by_name = {e["pilot_name"]: e["kills"] for e in deaths_list}

    # Merge all pilot names from both lists
    all_pilots = set(kills_by_name.keys()) | set(deaths_by_name.keys())

    merged = []
    for name in all_pilots:
        k = kills_by_name.get(name, 0)
        d = deaths_by_name.get(name, 0)
        kd = k / max(d, 1)
        merged.append({
            "pilot_name": name,
            "kills":      k,
            "deaths":     d,
            "kd":         round(kd, 2),
        })

    merged.sort(key=lambda x: x["kd"], reverse=True)

    results = []
    for rank, entry in enumerate(merged[:10], start=1):
        results.append({
            "rank":       rank,
            "pilot_name": entry["pilot_name"],
            "kills":      entry["kills"],
            "deaths":     entry["deaths"],
            "kd":         entry["kd"],
        })

    return results

def get_kills_against_character(victim_name: str) -> list[dict]:
    """
    Returns the top 10 Black Rabbits pilots by kill count
    against a victim whose name contains the given string (case-insensitive LIKE match).
    """
    return _query_kills_against(
        "victim_name LIKE ? AND final_blow_id != 0",
        (f"%{victim_name}%",)
    )


def get_kills_against_corp(corp_id: int) -> list[dict]:
    """
    Returns the top 10 Black Rabbits pilots by kill count
    against victims from a specific corporation (matched by corporation ID).
    """
    return _query_kills_against(
        "victim_corp = ? AND final_blow_id != 0",
        (str(corp_id),)
    )


def get_kills_against_alliance(alliance_id: int) -> list[dict]:
    """
    Returns the top 10 Black Rabbits pilots by kill count
    against victims from a specific alliance (matched by alliance ID).
    """
    return _query_kills_against(
        "victim_alliance_id = ? AND final_blow_id != 0",
        (alliance_id,)
    )


def _query_kills_against(where_clause: str, params: tuple) -> list[dict]:
    """
    Internal helper: returns top 10 Black Rabbits pilots by kill count
    against victims matching the provided WHERE clause.

    `where_clause` is always set by internal code, never by user input.
    User-supplied values are passed safely through `params` (parameterized).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT
            final_blow_name,
            final_blow_id,
            COUNT(*) as kill_count
        FROM kills
        WHERE {where_clause}
        GROUP BY final_blow_id, final_blow_name
        ORDER BY kill_count DESC
        LIMIT 10
    """, params)

    rows = cursor.fetchall()
    conn.close()

    results = []
    for rank, (name, char_id, count) in enumerate(rows, start=1):
        results.append({
            "rank":       rank,
            "pilot_name": name,
            "char_id":    char_id,
            "kills":      count,
            "zkb_url":    f"https://zkillboard.com/character/{char_id}/",
        })

    return results


def format_top10_embed_text(title: str, results: list[dict], label: str = "final blow") -> str:
    """
    Formats a top 10 list into a clean text block for Discord.
    Pass label='death' for the solo deaths leaderboard.
    """
    if not results:
        return f"No {label}s recorded for this period."

    lines = []
    medals = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}

    for entry in results:
        rank   = entry["rank"]
        name   = entry["pilot_name"]
        kills  = entry["kills"]
        medal  = medals.get(rank, f"`#{rank}`")
        lines.append(f"{medal} **{name}** \u2014 {kills} {label}{'s' if kills != 1 else ''}")

    return "\n".join(lines)

def search_character_victims(partial: str) -> list[dict]:
    """
    Returns up to 25 distinct victim names from kills
    that contain the partial string (case-insensitive).
    Ordered by how many times that victim appears (most killed first).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            victim_name,
            COUNT(*) as kill_count
        FROM kills
        WHERE victim_name LIKE ?
          AND victim_name IS NOT NULL
          AND victim_name != ''
          AND victim_name != 'Unknown'
        GROUP BY victim_name
        ORDER BY kill_count DESC
        LIMIT 25
    """, (f"%{partial}%",))

    rows = cursor.fetchall()
    conn.close()

    return [
        {"name": row[0], "type": "character", "count": row[1]}
        for row in rows
    ]


def search_corporations(partial: str) -> list[dict]:
    """
    Returns up to 25 corporations whose name or ticker
    contains the partial string (case-insensitive).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT corp_id, corp_name, ticker
        FROM corporations
        WHERE corp_name LIKE ?
           OR ticker LIKE ?
        ORDER BY corp_name ASC
        LIMIT 25
    """, (f"%{partial}%", f"%{partial}%"))

    rows = cursor.fetchall()
    conn.close()

    return [
        {"id": row[0], "name": row[1], "ticker": row[2], "type": "corporation"}
        for row in rows
    ]


def search_alliances(partial: str) -> list[dict]:
    """
    Returns up to 25 alliances whose name or ticker
    contains the partial string (case-insensitive).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT alliance_id, alliance_name, ticker
        FROM alliances
        WHERE alliance_name LIKE ?
           OR ticker LIKE ?
        ORDER BY alliance_name ASC
        LIMIT 25
    """, (f"%{partial}%", f"%{partial}%"))

    rows = cursor.fetchall()
    conn.close()

    return [
        {"id": row[0], "name": row[1], "ticker": row[2], "type": "alliance"}
        for row in rows
    ]

def get_top10_all_kills(period: str = "ytd") -> list[dict]:
    """
    Returns top 10 pilots by total kill participation (any attacker role)
    for the given period: 'ytd', 'month', or 'week'.
    """
    now = datetime.now(timezone.utc)

    if period == "ytd":
        start = datetime(now.year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    elif period == "month":
        start = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
    elif period == "week":
        days_since_monday = now.weekday()
        monday = now - timedelta(days=days_since_monday)
        start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Unknown period: {period}")

    return _query_top10_all_kills(start.isoformat(), now.isoformat())

def _query_top10_all_kills(start_iso: str, end_iso: str) -> list[dict]:
    """
    Internal helper: queries the attackers table for top 10 pilots
    by distinct kill participation between start_iso and end_iso.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            character_name,
            character_id,
            COUNT(DISTINCT kill_id) as kill_count
        FROM attackers
        WHERE kill_timestamp >= ?
          AND kill_timestamp <= ?
          AND character_id != 0
          AND character_name IS NOT NULL
          AND character_name != ''
          AND character_name != 'Unknown Pilot'
        GROUP BY character_id, character_name
        ORDER BY kill_count DESC
        LIMIT 10
    """, (start_iso, end_iso))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for rank, (name, char_id, count) in enumerate(rows, start=1):
        results.append({
            "rank":       rank,
            "pilot_name": name,
            "char_id":    char_id,
            "kills":      count,
            "zkb_url":    f"https://zkillboard.com/character/{char_id}/",
        })

    return results

def search_all_pilots(partial: str) -> list[dict]:
    """
    Returns up to 25 distinct pilot names from the attackers table
    that contain the partial string (case-insensitive).
    Ordered by total kill count (most active first).
    Used for /mystats autocomplete.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            character_name,
            character_id,
            COUNT(DISTINCT kill_id) as kill_count
        FROM attackers
        WHERE character_name LIKE ?
          AND character_id != 0
          AND character_name IS NOT NULL
          AND character_name != ''
          AND character_name != 'Unknown Pilot'
        GROUP BY character_id, character_name
        ORDER BY kill_count DESC
        LIMIT 25
    """, (f"%{partial}%",))

    rows = cursor.fetchall()
    conn.close()

    return [
        {"name": row[0], "char_id": row[1], "count": row[2]}
        for row in rows
    ]


def get_pilot_stats(character_name: str, character_id: int, period: str) -> dict:
    """
    Returns personal stats for a single pilot for the given period.
    period: 'ytd', 'month', or 'week'

    Returns a dict with:
      - kill_participation: distinct kills the pilot appeared on as any attacker
      - final_blows:        kills where this pilot had the final blow
      - solo_kills:         solo kills where this pilot had the final blow
      - solo_losses:        solo losses where this pilot was the victim
    """
    now = datetime.now(timezone.utc)

    if period == "ytd":
        start = datetime(now.year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    elif period == "month":
        start = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
    elif period == "week":
        days_since_monday = now.weekday()
        monday = now - timedelta(days=days_since_monday)
        start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Unknown period: {period}")

    start_iso = start.isoformat()
    end_iso   = now.isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    # Kill participation — any role on the kill (from attackers table)
    cursor.execute("""
        SELECT COUNT(DISTINCT kill_id)
        FROM attackers
        WHERE character_id = ?
          AND kill_timestamp >= ?
          AND kill_timestamp <= ?
    """, (character_id, start_iso, end_iso))
    kill_participation = cursor.fetchone()[0] or 0

    # Final blows — this pilot delivered the killing shot (kills only, not losses)
    cursor.execute("""
        SELECT COUNT(*)
        FROM kills
        WHERE final_blow_id = ?
          AND kill_time >= ?
          AND kill_time <= ?
          AND is_loss = 0
    """, (character_id, start_iso, end_iso))
    final_blows = cursor.fetchone()[0] or 0

    # Solo kills — solo final blows (kills only)
    cursor.execute("""
        SELECT COUNT(*)
        FROM kills
        WHERE final_blow_id = ?
          AND kill_time >= ?
          AND kill_time <= ?
          AND is_solo = 1
          AND is_loss = 0
    """, (character_id, start_iso, end_iso))
    solo_kills = cursor.fetchone()[0] or 0

    # Solo losses — this pilot was the victim on a solo loss
    cursor.execute("""
        SELECT COUNT(*)
        FROM kills
        WHERE victim_name = ?
          AND kill_time >= ?
          AND kill_time <= ?
          AND is_loss = 1
          AND is_solo = 1
    """, (character_name, start_iso, end_iso))
    solo_losses = cursor.fetchone()[0] or 0

    conn.close()

    return {
        "kill_participation": kill_participation,
        "final_blows":        final_blows,
        "solo_kills":         solo_kills,
        "solo_losses":        solo_losses,
    }
