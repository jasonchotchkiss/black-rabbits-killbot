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
            zkb_url             TEXT
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
            zkb_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
