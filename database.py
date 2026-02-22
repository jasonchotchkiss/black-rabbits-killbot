import sqlite3
import os

# The database file will live in the same directory as the bot
DB_PATH = os.path.join(os.path.dirname(__file__), "killboard.db")


def get_connection():
    """Open and return a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """
    Create the kills table if it does not already exist.
    Also applies any pending schema migrations.
    This is safe to call every time the bot starts.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kills (
            kill_id             INTEGER PRIMARY KEY,
            kill_time           TEXT NOT NULL,
            final_blow_name     TEXT NOT NULL,
            final_blow_id       INTEGER NOT NULL,
            ship_type_id        INTEGER,
            victim_name         TEXT,
            victim_corp         TEXT,
            victim_alliance_id  INTEGER DEFAULT 0,
            solar_system_id     INTEGER,
            zkb_url             TEXT,
            zkb_hash            TEXT DEFAULT '',
            is_solo             INTEGER DEFAULT 0
        )
    """)

    # Lookup tables for corp/alliance names (for validation + autocomplete)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS corporations (
            corp_id   INTEGER PRIMARY KEY,
            corp_name TEXT NOT NULL,
            ticker    TEXT DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alliances (
            alliance_id   INTEGER PRIMARY KEY,
            alliance_name TEXT NOT NULL,
            ticker        TEXT DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attackers (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            kill_id         INTEGER NOT NULL,
            character_id    INTEGER NOT NULL,
            character_name  TEXT NOT NULL,
            damage_done     INTEGER DEFAULT 0,
            is_final_blow   INTEGER DEFAULT 0,
            kill_timestamp  TEXT NOT NULL,
            UNIQUE (kill_id, character_id),
            FOREIGN KEY (kill_id) REFERENCES kills(kill_id)
        )
    """)

    # Migration: add victim_alliance_id to databases that predate this column.
    # ALTER TABLE fails silently if the column already exists.
    try:
        cursor.execute("ALTER TABLE kills ADD COLUMN victim_alliance_id INTEGER DEFAULT 0")
        conn.commit()
        print("Migration applied: added victim_alliance_id column.")
    except sqlite3.OperationalError:
        pass  # Column already exists — safe to ignore

    try:
        cursor.execute("ALTER TABLE kills ADD COLUMN zkb_hash TEXT DEFAULT ''")
        conn.commit()
        print("Migration applied: added zkb_hash column.")
    except sqlite3.OperationalError:
        pass  # Column already exists — safe to ignore
    try:
        cursor.execute("ALTER TABLE kills ADD COLUMN is_solo INTEGER DEFAULT 0")
        conn.commit()
        print("Migration applied: added is_solo column.")
    except sqlite3.OperationalError:
        pass  # Column already exists — safe to ignore

    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")


def save_kill(kill_data: dict):
    """
    Insert a single kill into the database.
    Ignores the insert if the kill_id already exists (no duplicates).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO kills (
            kill_id,
            kill_time,
            final_blow_name,
            final_blow_id,
            ship_type_id,
            victim_name,
            victim_corp,
            victim_alliance_id,
            solar_system_id,
            zkb_url,
            zkb_hash,
            is_solo       
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        kill_data["kill_id"],
        kill_data["kill_time"],
        kill_data["final_blow_name"],
        kill_data["final_blow_id"],
        kill_data.get("ship_type_id"),
        kill_data.get("victim_name"),
        kill_data.get("victim_corp"),
        kill_data.get("victim_alliance_id", 0),
        kill_data.get("solar_system_id"),
        kill_data.get("zkb_url"),
        kill_data.get("zkb_hash", ""),
        kill_data.get("is_solo", 0),
    ))

    conn.commit()
    conn.close()

def save_attackers(kill_id: int, kill_timestamp: str, attackers: list[dict]):
    """
    Insert attacker rows for a given kill.
    Skips attackers with no character_id (NPCs).
    Safe to call multiple times — uses INSERT OR IGNORE.
    """
    conn = get_connection()
    cursor = conn.cursor()

    for a in attackers:
        character_id = a.get("character_id", 0)
        if not character_id:
            continue
        cursor.execute("""
            INSERT OR IGNORE INTO attackers (
                kill_id,
                character_id,
                character_name,
                damage_done,
                is_final_blow,
                kill_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            kill_id,
            character_id,
            a.get("character_name", "Unknown Pilot"),
            a.get("damage_done", 0),
            a.get("is_final_blow", 0),
            kill_timestamp,
        ))
    conn.commit()
    conn.close()


def get_kill_count():
    """Return the total number of kills stored in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM kills")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_corporation_name(corp_id: int) -> str | None:
    """
    Return the corporation name for a given corp_id, or None if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT corp_name FROM corporations WHERE corp_id = ?",
        (corp_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_alliance_name(alliance_id: int) -> str | None:
    """
    Return the alliance name for a given alliance_id, or None if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT alliance_name FROM alliances WHERE alliance_id = ?",
        (alliance_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def upsert_corporation(corp_id: int, corp_name: str, ticker: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO corporations (corp_id, corp_name, ticker)
        VALUES (?, ?, ?)
        ON CONFLICT(corp_id) DO UPDATE SET
            corp_name = excluded.corp_name,
            ticker    = excluded.ticker
    """, (corp_id, corp_name, ticker))
    conn.commit()
    conn.close()


def upsert_alliance(alliance_id: int, alliance_name: str, ticker: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alliances (alliance_id, alliance_name, ticker)
        VALUES (?, ?, ?)
        ON CONFLICT(alliance_id) DO UPDATE SET
            alliance_name = excluded.alliance_name,
            ticker        = excluded.ticker
    """, (alliance_id, alliance_name, ticker))
    conn.commit()
    conn.close()


def get_missing_corp_ids(limit: int = 1500) -> list[int]:
    """
    Corp IDs that appear in kills.victim_corp but are not yet in corporations.
    victim_corp is stored as TEXT today, so we CAST it to INTEGER.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT CAST(victim_corp AS INTEGER) AS corp_id
        FROM kills
        WHERE victim_corp IS NOT NULL
          AND victim_corp != ''
          AND CAST(victim_corp AS INTEGER) != 0
          AND CAST(victim_corp AS INTEGER) NOT IN (SELECT corp_id FROM corporations)
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows if r[0] is not None]


def get_missing_alliance_ids(limit: int = 1000) -> list[int]:
    """
    Alliance IDs that appear in kills.victim_alliance_id but are not yet in alliances.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT victim_alliance_id
        FROM kills
        WHERE victim_alliance_id IS NOT NULL
          AND victim_alliance_id != 0
          AND victim_alliance_id NOT IN (SELECT alliance_id FROM alliances)
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows if r[0] is not None]

def get_missing_character_ids(limit: int = 2000) -> list[int]:
    """
    Character IDs in attackers that still have 'Unknown Pilot' as their name.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT character_id FROM attackers
        WHERE character_name = 'Unknown Pilot'
          AND character_id IS NOT NULL
          AND character_id != 0
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def upsert_character_name(character_id: int, name: str):
    """
    Update the character_name for all attacker rows with a matching character_id
    that still show 'Unknown Pilot'.
    """
    conn = get_connection()
    conn.execute("""
        UPDATE attackers SET character_name = ?
        WHERE character_id = ? AND character_name = 'Unknown Pilot'
    """, (name, character_id))
    conn.commit()
    conn.close()

