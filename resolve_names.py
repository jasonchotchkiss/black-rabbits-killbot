import asyncio
import aiohttp
from database import get_missing_corp_ids, get_missing_alliance_ids, upsert_corporation, upsert_alliance

ESI_BASE = "https://esi.evetech.net/latest"
USER_AGENT = "BlackRabbitsKillbot/1.0 (Discord bot; github.com/jasonchotchkiss)"


async def resolve_corporation(session: aiohttp.ClientSession, corp_id: int) -> bool:
    """
    Fetch corporation name and ticker from ESI by corp_id.
    Returns True on success, False on failure.
    """
    url = f"{ESI_BASE}/corporations/{corp_id}/"
    headers = {"User-Agent": USER_AGENT}

    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json(content_type=None)
                name   = data.get("name", "")
                ticker = data.get("ticker", "")
                if name:
                    upsert_corporation(corp_id, name, ticker)
                    return True
            else:
                print(f"  ESI error {response.status} for corp_id {corp_id}")
    except Exception as e:
        print(f"  Exception for corp_id {corp_id}: {e}")

    return False


async def resolve_alliance(session: aiohttp.ClientSession, alliance_id: int) -> bool:
    """
    Fetch alliance name and ticker from ESI by alliance_id.
    Returns True on success, False on failure.
    """
    url = f"{ESI_BASE}/alliances/{alliance_id}/"
    headers = {"User-Agent": USER_AGENT}

    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json(content_type=None)
                name   = data.get("name", "")
                ticker = data.get("ticker", "")
                if name:
                    upsert_alliance(alliance_id, name, ticker)
                    return True
            else:
                print(f"  ESI error {response.status} for alliance_id {alliance_id}")
    except Exception as e:
        print(f"  Exception for alliance_id {alliance_id}: {e}")

    return False


async def run_backfill():
    """
    Main backfill function.
    Resolves all corp and alliance IDs in kills that are missing from lookup tables.
    Safe to run multiple times — only resolves what is missing.
    """
    corp_ids     = get_missing_corp_ids()
    alliance_ids = get_missing_alliance_ids()

    print(f"Corps to resolve:    {len(corp_ids)}")
    print(f"Alliances to resolve: {len(alliance_ids)}")

    if not corp_ids and not alliance_ids:
        print("Nothing to resolve. Tables are already up to date.")
        return

    async with aiohttp.ClientSession() as session:

        # --- Corporations ---
        corp_ok   = 0
        corp_fail = 0
        for i, corp_id in enumerate(corp_ids, start=1):
            success = await resolve_corporation(session, corp_id)
            if success:
                corp_ok += 1
            else:
                corp_fail += 1
            # Progress update every 25
            if i % 25 == 0:
                print(f"  Corps: {i}/{len(corp_ids)} processed...")
            await asyncio.sleep(0.3)

        # --- Alliances ---
        ally_ok   = 0
        ally_fail = 0
        for i, alliance_id in enumerate(alliance_ids, start=1):
            success = await resolve_alliance(session, alliance_id)
            if success:
                ally_ok += 1
            else:
                ally_fail += 1
            if i % 25 == 0:
                print(f"  Alliances: {i}/{len(alliance_ids)} processed...")
            await asyncio.sleep(0.3)

    print()
    print(f"Done.")
    print(f"  Corps:    {corp_ok} resolved, {corp_fail} failed")
    print(f"  Alliances: {ally_ok} resolved, {ally_fail} failed")


if __name__ == "__main__":
    asyncio.run(run_backfill())
