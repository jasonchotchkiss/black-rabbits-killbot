import asyncio
import aiohttp
from database import (
    get_missing_corp_ids,
    get_missing_alliance_ids,
    get_missing_character_ids,
    upsert_corporation,
    upsert_alliance,
    upsert_character_name,
)

ESI_BASE   = "https://esi.evetech.net/latest"
USER_AGENT = "BlackRabbitsKillbot/1.0 (Discord bot; github.com/jasonchotchkiss)"


async def resolve_character(session: aiohttp.ClientSession, character_id: int) -> bool:
    url     = f"{ESI_BASE}/characters/{character_id}/"
    headers = {"User-Agent": USER_AGENT}
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json(content_type=None)
                name = data.get("name", "")
                if name:
                    upsert_character_name(character_id, name)
                    return True
            else:
                print(f"  ESI error {response.status} for character_id {character_id}")
    except Exception as e:
        print(f"  Exception for character_id {character_id}: {e}")
    return False


async def resolve_corporation(session: aiohttp.ClientSession, corp_id: int) -> bool:
    url     = f"{ESI_BASE}/corporations/{corp_id}/"
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
    url     = f"{ESI_BASE}/alliances/{alliance_id}/"
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
    Resolves all missing character, corp, and alliance names.
    Safe to run multiple times — only resolves what is missing.
    """
    character_ids = get_missing_character_ids()
    corp_ids      = get_missing_corp_ids()
    alliance_ids  = get_missing_alliance_ids()

    print(f"Characters to resolve: {len(character_ids)}")
    print(f"Corps to resolve:      {len(corp_ids)}")
    print(f"Alliances to resolve:  {len(alliance_ids)}")

    if not character_ids and not corp_ids and not alliance_ids:
        print("Nothing to resolve. Tables are already up to date.")
        return

    async with aiohttp.ClientSession() as session:

        # --- Characters ---
        char_ok = char_fail = 0
        for i, char_id in enumerate(character_ids, start=1):
            success = await resolve_character(session, char_id)
            if success:
                char_ok += 1
            else:
                char_fail += 1
            if i % 25 == 0:
                print(f"  Characters: {i}/{len(character_ids)} processed...")
            await asyncio.sleep(0.3)

        # --- Corporations ---
        corp_ok = corp_fail = 0
        for i, corp_id in enumerate(corp_ids, start=1):
            success = await resolve_corporation(session, corp_id)
            if success:
                corp_ok += 1
            else:
                corp_fail += 1
            if i % 25 == 0:
                print(f"  Corps: {i}/{len(corp_ids)} processed...")
            await asyncio.sleep(0.3)

        # --- Alliances ---
        ally_ok = ally_fail = 0
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
    print("Done.")
    print(f"  Characters: {char_ok} resolved, {char_fail} failed")
    print(f"  Corps:      {corp_ok} resolved, {corp_fail} failed")
    print(f"  Alliances:  {ally_ok} resolved, {ally_fail} failed")


if __name__ == "__main__":
    asyncio.run(run_backfill())
