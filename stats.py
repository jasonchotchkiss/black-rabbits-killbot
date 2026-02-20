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


def format_top10_embed_text(title: str, results: list[dict]) -> str:
    """
    Formats a top 10 list into a clean text block for Discord.
    We'll use this in the embed message later.
    """
    if not results:
        return "No kills recorded for this period."

    lines = []
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    for entry in results:
        rank   = entry["rank"]
        name   = entry["pilot_name"]
        kills  = entry["kills"]
        medal  = medals.get(rank, f"`#{rank}`")
        lines.append(f"{medal} **{name}** — {kills} final blow{'s' if kills != 1 else ''}")

    return "\n".join(lines)
