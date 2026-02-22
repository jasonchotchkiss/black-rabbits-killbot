import asyncio
from zkillboard import fetch_and_extract_kills, fetch_and_extract_losses
from database import init_db, save_kill, save_attackers, get_kill_count
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

    # Save each kill and its attackers to the database
    for kill in kills:
        save_kill(kill)
        if kill.get("attackers"):
            save_attackers(kill["kill_id"], kill["kill_time"], kill["attackers"])

    count_after = get_kill_count()
    new_kills   = count_after - count_before

    print(f"Kills in database after sync : {count_after}")
    print(f"New kills added              : {new_kills}")

    # Resolve any new corp/alliance names that appeared in this sync
    if new_kills > 0:
        print("Resolving new corp/alliance names...")
        await run_backfill()

    print("=== Sync complete ===")

async def sync_losses(max_pages: int = 5):
    """
    Fetch losses from zKillboard/ESI and save any new ones to the database.
    Skips losses already in the database (INSERT OR IGNORE handles duplicates).
    """
    print("=== Black Rabbits Killbot - Loss Sync ===")

    init_db()

    count_before = get_kill_count()
    print(f"Kills in database before loss sync: {count_before}")

    losses = await fetch_and_extract_losses(max_pages=max_pages)

    if not losses:
        print("No losses returned from API. Nothing to save.")
        return

    for loss in losses:
        save_kill(loss)
        if loss.get("attackers"):
            save_attackers(loss["kill_id"], loss["kill_time"], loss["attackers"])

    count_after = get_kill_count()
    new_losses  = count_after - count_before

    print(f"Kills in database after loss sync : {count_after}")
    print(f"New losses added                  : {new_losses}")

    if new_losses > 0:
        print("Resolving new names from losses...")
        await run_backfill()

    print("=== Loss sync complete ===")

if __name__ == "__main__":
    # When run directly, fetch 3 pages (up to 600 kills) as a test
    # For the initial full backfill we will increase this later
    asyncio.run(sync_kills(max_pages=3))
