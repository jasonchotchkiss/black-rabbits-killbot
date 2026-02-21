import asyncio
from zkillboard import fetch_and_extract_kills
from database import init_db, save_kill, get_kill_count
from resolve_names import run_backfill


async def sync_kills(max_pages: int = 5):
    """
    Fetch kills from zKillboard/ESI and save any new ones to the database.
    Skips kills already in the database (INSERT OR IGNORE handles duplicates).
    """
    print("=== Black Rabbits Killbot - Kill Sync ===")

    # Make sure the database and table exist
    init_db()

    count_before = get_kill_count()
    print(f"Kills in database before sync: {count_before}")

    # Fetch kills from zKillboard + ESI
    kills = await fetch_and_extract_kills(max_pages=max_pages)

    if not kills:
        print("No kills returned from API. Nothing to save.")
        return

    # Save each kill to the database
    for kill in kills:
        save_kill(kill)

    count_after = get_kill_count()
    new_kills   = count_after - count_before

    print(f"Kills in database after sync : {count_after}")
    print(f"New kills added              : {new_kills}")

    # Resolve any new corp/alliance names that appeared in this sync
    if new_kills > 0:
        print("Resolving new corp/alliance names...")
        await run_backfill()

    print("=== Sync complete ===")


if __name__ == "__main__":
    # When run directly, fetch 3 pages (up to 600 kills) as a test
    # For the initial full backfill we will increase this later
    asyncio.run(sync_kills(max_pages=3))
