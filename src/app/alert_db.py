"""SQLite alert database for triage persistence and export (T-P8-05)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

DEFAULT_DB_PATH = Path("data/processed/alerts.db")


def get_db_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Get connection to SQLite alert database, creating tables if necessary."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sample_id TEXT NOT NULL,
                verdict TEXT NOT NULL,
                confidence REAL NOT NULL,
                top_reason TEXT,
                category TEXT,
                mitre_technique TEXT,
                status TEXT NOT NULL DEFAULT 'NEW',
                analyst_notes TEXT DEFAULT ''
            )
        """)
    return conn


def log_alert(
    sample_id: str,
    verdict: str,
    confidence: float,
    top_reason: str = "",
    category: str = "",
    mitre_technique: str = "",
    status: str = "NEW",
    analyst_notes: str = "",
    db_path: Path = DEFAULT_DB_PATH,
) -> int:
    """Log an alert into SQLite database."""
    conn = get_db_connection(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO alerts (timestamp, sample_id, verdict, confidence, top_reason, category, mitre_technique, status, analyst_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (now, sample_id, verdict, float(confidence), top_reason, category, mitre_technique, status, analyst_notes),
        )
        return cursor.lastrowid


def get_alerts_dataframe(db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Retrieve all alert records as a DataFrame."""
    conn = get_db_connection(db_path)
    df = pd.read_sql_query("SELECT * FROM alerts ORDER BY id DESC", conn)
    conn.close()
    return df


def update_alert_status(
    alert_id: int,
    status: str,
    analyst_notes: Optional[str] = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> None:
    """Update alert review status and analyst notes."""
    conn = get_db_connection(db_path)
    with conn:
        if analyst_notes is not None:
            conn.execute(
                "UPDATE alerts SET status = ?, analyst_notes = ? WHERE id = ?",
                (status, analyst_notes, alert_id),
            )
        else:
            conn.execute(
                "UPDATE alerts SET status = ? WHERE id = ?",
                (status, alert_id),
            )
    conn.close()
