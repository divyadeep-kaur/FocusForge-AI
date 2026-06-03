import os
import sqlite3
from contextlib import closing


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        xp INTEGER NOT NULL DEFAULT 0,
        level TEXT NOT NULL DEFAULT 'Bronze',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0,
        completed_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS streaks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        activity_date TEXT NOT NULL,
        completed_count INTEGER NOT NULL DEFAULT 0,
        UNIQUE(user_id, activity_date),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        xp_required INTEGER NOT NULL,
        description TEXT NOT NULL,
        tier TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        friend_id INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, friend_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (friend_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """

    rewards = [
        ("Deep Work Badge", 100, "Complete your first serious week of focused work.", "Bronze"),
        ("Momentum Theme", 250, "Unlock a brighter dashboard accent palette.", "Silver"),
        ("Focus Forge Banner", 500, "Earn a profile banner for consistent planning.", "Gold"),
        ("Sapphire Mentor", 1000, "Unlock premium AI coach prompts and status styling.", "Sapphire"),
    ]

    with closing(get_db_connection()) as conn:
        conn.executescript(schema)
        conn.executemany(
            "INSERT OR IGNORE INTO rewards (name, xp_required, description, tier) VALUES (?, ?, ?, ?)",
            rewards,
        )
        conn.commit()


def level_for_xp(xp):
    if xp >= 1000:
        return "Sapphire"
    if xp >= 500:
        return "Gold"
    if xp >= 250:
        return "Silver"
    return "Bronze"
