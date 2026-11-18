"""SQLite persistence layer for log sessions and entries."""

import os
import sqlite3
from datetime import datetime
from typing import Optional

from parser import LogEntry, compute_counts, filter_entries

DB_PATH = os.environ.get("LOG_DB_PATH", os.path.join(os.path.dirname(__file__), "logs.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    timestamp TEXT,
    level TEXT,
    message TEXT
);
CREATE INDEX IF NOT EXISTS idx_entries_session ON entries(session_id);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def store_session(filename: str, entries: list[LogEntry]) -> int:
    """Store a parsed session and its entries. Returns the session id."""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO sessions (filename, created_at) VALUES (?, ?)",
            (filename, created_at),
        )
        session_id = int(cur.lastrowid)
        conn.executemany(
            "INSERT INTO entries (session_id, timestamp, level, message) VALUES (?, ?, ?, ?)",
            [(session_id, e.timestamp, e.level, e.message) for e in entries],
        )
    return session_id


def list_sessions() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT s.id, s.filename, s.created_at,
                   COUNT(e.id) AS entry_count
            FROM sessions s
            LEFT JOIN entries e ON e.session_id = s.id
            GROUP BY s.id
            ORDER BY s.id DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def get_entries(session_id: int) -> list[LogEntry]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT timestamp, level, message FROM entries WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
    return [LogEntry(r["timestamp"], r["level"], r["message"] or "") for r in rows]


def get_session_logs(
    session_id: int,
    level: Optional[str] = None,
    query: Optional[str] = None,
) -> dict:
    entries = get_entries(session_id)
    counts = compute_counts(entries)
    filtered = filter_entries(entries, level=level, query=query)
    return {
        "counts": {"TOTAL": len(entries), **counts},
        "logs": [
            {"timestamp": e.timestamp, "level": e.level, "message": e.message}
            for e in filtered
        ],
    }


def delete_session(session_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cur.rowcount > 0
