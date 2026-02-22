import aiohttp
import asyncio

# zKillboard API base URL
ZKILL_BASE = "https://zkillboard.com/api"

# ESI (EVE Swagger Interface) base URL - EVE's official API
ESI_BASE = "https://esi.evetech.net/latest"

# Alliance ID for Black Rabbits
ALLIANCE_ID = 99012611

# Both APIs require a descriptive User-Agent header
USER_AGENT = "BlackRabbitsKillbot/1.0 (Discord bot; github.com/jasonchotchkiss)"
CAPSULE_TYPE_IDS = {670, 33328}


async def fetch_zkill_page(session: aiohttp.ClientSession, page: int = 1) -> list:
    """
    Fetch one page of kill references from zKillboard.
    Returns a list of dicts, each containing killmail_id and zkb metadata.
    Each page returns up to 200 entries.
    """
    url = f"{ZKILL_BASE}/kills/allianceID/{ALLIANCE_ID}/page/{page}/"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip"
    }

    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json(content_type=None)
            return data if data else []
        else:
            print(f"zKillboard error: HTTP {response.status} on page {page}")
            return []


async def fetch_esi_killmail(
    session: aiohttp.ClientSession,
    killmail_id: int,
    killmail_hash: str
) -> dict | None:
    """
    Fetch full killmail details from ESI using the killmail_id and hash.
    Returns the full killmail dict, or None on error.
    """
    url = f"{ESI_BASE}/killmails/{killmail_id}/{killmail_hash}/"
    headers = {"User-Agent": USER_AGENT}

    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json(content_type=None)
        else:
            print(f"ESI error: HTTP {response.status} for kill {killmail_id}")
            return None


async def resolve_character_name(
    session: aiohttp.ClientSession,
    character_id: int
) -> str:
    """
    Look up a character's name from ESI using their character_id.
    Returns the name string, or 'Unknown Pilot' if the lookup fails.
    """
    if not character_id or character_id == 0:
        return "Unknown Pilot"

    url = f"{ESI_BASE}/characters/{character_id}/"
    headers = {"User-Agent": USER_AGENT}

    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json(content_type=None)
            return data.get("name", "Unknown Pilot")
        else:
            return "Unknown Pilot"


async def resolve_entity_name(name: str) -> tuple[str, int] | None:
    """
    Use ESI /universe/ids/ to resolve a name string to an entity type and ID.
    Returns ("character", id), ("corporation", id), or ("alliance", id).
    Returns None if the name is not found or on any error.

    Note: ESI requires an exact match — partial names will return nothing.
    """
    url = f"{ESI_BASE}/universe/ids/?datasource=tranquility"
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=[name], headers=headers) as response:
                if response.status != 200:
                    return None
                data = await response.json(content_type=None)

                if data.get("characters"):
                    return ("character", data["characters"][0]["id"])
                elif data.get("corporations"):
                    return ("corporation", data["corporations"][0]["id"])
                elif data.get("alliances"):
                    return ("alliance", data["alliances"][0]["id"])
                else:
                    return None
    except Exception as e:
        print(f"ESI resolve_entity_name error for '{name}': {e}")
        return None


def extract_kill_data(zkb_entry: dict, esi_killmail: dict) -> dict | None:
    """
    Combine zKillboard metadata and ESI killmail data into a clean dict
    ready to be saved to the database.
    Returns None if the victim is a capsule (pod) or no final blow attacker found.
    """
    kill_id   = esi_killmail.get("killmail_id")
    kill_time = esi_killmail.get("killmail_time")   # e.g. "2024-01-15T12:34:56Z"
    victim    = esi_killmail.get("victim", {})
    attackers = esi_killmail.get("attackers", [])

    # Skip pod kills
    if victim.get("ship_type_id") in CAPSULE_TYPE_IDS:
        return None

    # Find the attacker who landed the final blow
    final_blow_attacker = next(
        (a for a in attackers if a.get("final_blow") is True),
        None
    )

    if not final_blow_attacker:
        return None

    # NPC attackers won't have a character_id — we'll store 0 for them
    final_blow_id   = final_blow_attacker.get("character_id", 0)
    final_blow_name = final_blow_attacker.get("character_name", "Unknown Pilot")

    return {
        "kill_id":            kill_id,
        "kill_time":          kill_time,
        "final_blow_id":      final_blow_id,
        "final_blow_name":    final_blow_name,
        "ship_type_id":       victim.get("ship_type_id"),
        "victim_name":        victim.get("character_name", "Unknown"),
        "victim_corp":        str(victim.get("corporation_id", "")),
        "victim_alliance_id": victim.get("alliance_id", 0),
        "solar_system_id":    esi_killmail.get("solar_system_id"),
        "zkb_url":            f"https://zkillboard.com/kill/{kill_id}/",
        "zkb_hash":           zkb_entry.get("zkb", {}).get("hash", ""),
        "is_solo":            1 if zkb_entry.get("zkb", {}).get("solo", False) else 0,
    }


async def fetch_and_extract_kills(max_pages: int = 5) -> list:
    """
    Main function: fetch kill references from zKillboard, then enrich each
    one with full data from ESI.

    Returns a flat list of cleaned kill dicts ready for the database.
    max_pages=5 gives up to 1000 kills per run.
    """
    all_kills = []

    async with aiohttp.ClientSession() as session:
        for page in range(1, max_pages + 1):
            print(f"Fetching zKillboard page {page}...")
            zkill_entries = await fetch_zkill_page(session, page)

            if not zkill_entries:
                print(f"No more entries after page {page - 1}. Stopping.")
                break

            print(f"  Got {len(zkill_entries)} kill references. Fetching full details from ESI...")

            for entry in zkill_entries:
                kill_id = entry.get("killmail_id")
                zkb     = entry.get("zkb", {})
                khash   = zkb.get("hash")

                if not kill_id or not khash:
                    continue

                # Fetch full killmail from ESI
                esi_data = await fetch_esi_killmail(session, kill_id, khash)

                if not esi_data:
                    continue

                clean = extract_kill_data(entry, esi_data)
                if clean:
                    # Resolve final blow name if missing
                    if clean["final_blow_name"] == "Unknown Pilot" and clean["final_blow_id"] != 0:
                        clean["final_blow_name"] = await resolve_character_name(
                            session, clean["final_blow_id"]
                        )
                        await asyncio.sleep(0.1)

                    # Resolve victim name if missing
                    victim_id = esi_data.get("victim", {}).get("character_id", 0)
                    if clean["victim_name"] == "Unknown" and victim_id != 0:
                        clean["victim_name"] = await resolve_character_name(
                            session, victim_id
                        )
                        await asyncio.sleep(0.1)

                    all_kills.append(clean)

                # Be polite to ESI - small pause between each killmail fetch
                await asyncio.sleep(0.2)

            print(f"  Page {page} processed. Running total: {len(all_kills)} kills.")

            # Pause between zKillboard pages
            if page < max_pages:
                await asyncio.sleep(1)

    print(f"Done. Total kills fetched and extracted: {len(all_kills)}")
    return all_kills
