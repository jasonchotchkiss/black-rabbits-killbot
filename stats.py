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


def _query_top10(start_iso: str, end_iso: str) -> list[dict]:
    """
    Internal helper: queries the database for top 10 pilots
    by final blow count between start_iso and end_iso timestamps.

    Returns a list of dicts with rank, pilot name, and kill count.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            final_blow_name,
            final_blow_id,
            COUNT(*) as kill_count
        FROM kills
        WHERE kill_time >= ?
          AND kill_time <= ?
          AND final_blow_id != 0
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


def format_top10_embed_text(title: str, results: list[dict]) -> str:
    """
    Formats a top 10 list into a clean text block for Discord.
    We'll use this in the embed message later.
    """
    if not results:
        return "No kills recorded for this period."

    lines = []
    medals = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}

    for entry in results:
        rank   = entry["rank"]
        name   = entry["pilot_name"]
        kills  = entry["kills"]
        medal  = medals.get(rank, f"`#{rank}`")
        lines.append(f"{medal} **{name}** \u2014 {kills} final blow{'s' if kills != 1 else ''}")

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
