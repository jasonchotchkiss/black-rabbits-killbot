import asyncio
import aiohttp
from database import get_connection
from zkillboard import fetch_esi_killmail, resolve_character_name, USER_AGENT

ZKILL_BASE = "https://zkillboard.com/api"


async def fetch_zkill_hash(session: aiohttp.ClientSession, kill_id: int) -> str:
    """Fetch the zkb hash for a single kill_id from zKillboard."""
    url = f"{ZKILL_BASE}/kills/killID/{kill_id}/"
    headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json(content_type=None)
            if data and isinstance(data, list):
                return data[0].get("zkb", {}).get("hash", "")
        return ""


async def backfill():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT kill_id
        FROM kills
        WHERE victim_name = 'Unknown'
           OR victim_name IS NULL
    """)
    rows = cursor.fetchall()
    conn.close()

    total = len(rows)
    print(f"Found {total} kills to backfill.")

    if total == 0:
        print("Nothing to do.")
        return

    updated = 0
    skipped = 0

    async with aiohttp.ClientSession() as session:
        for i, (kill_id,) in enumerate(rows, start=1):
            # Step 1: get hash from zKillboard
            zkb_hash = await fetch_zkill_hash(session, kill_id)
            await asyncio.sleep(0.3)

            if not zkb_hash:
                print(f"[{i}/{total}] SKIP kill {kill_id} — no hash from zKillboard")
                skipped += 1
                continue

            # Step 2: fetch full killmail from ESI
            esi = await fetch_esi_killmail(session, kill_id, zkb_hash)
            await asyncio.sleep(0.2)

            if not esi:
                print(f"[{i}/{total}] SKIP kill {kill_id} — ESI returned nothing")
                skipped += 1
                continue

            victim = esi.get("victim", {})
            victim_char_id  = victim.get("character_id", 0)
            victim_alliance = victim.get("alliance_id", 0)

            # Step 3: resolve victim name
            if victim_char_id and victim_char_id != 0:
                victim_name = await resolve_character_name(session, victim_char_id)
                await asyncio.sleep(0.1)
            else:
                victim_name = "Unknown"

            # Step 4: update DB
            conn = get_connection()
            conn.execute("""
                UPDATE kills
                SET victim_name = ?,
                    victim_alliance_id = ?,
                    zkb_hash = ?
                WHERE kill_id = ?
            """, (victim_name, victim_alliance, zkb_hash, kill_id))
            conn.commit()
            conn.close()

            updated += 1
            if i % 25 == 0:
                print(f"  [{i}/{total}] {updated} updated, {skipped} skipped")

            await asyncio.sleep(0.2)

    print(f"\nDone. {updated} kills updated, {skipped} skipped.")


if __name__ == "__main__":
    asyncio.run(backfill())
