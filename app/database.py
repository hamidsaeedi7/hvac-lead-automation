import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def database_path() -> Path:
    raw = os.getenv("HVAC_DATABASE_PATH", "data/hvac_demo.db")
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(database_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                service_type TEXT NOT NULL,
                postal_code TEXT NOT NULL,
                message TEXT NOT NULL,
                preferred_contact TEXT NOT NULL,
                priority TEXT NOT NULL,
                score INTEGER NOT NULL,
                reason TEXT NOT NULL,
                assigned_to TEXT NOT NULL,
                status TEXT NOT NULL,
                recommended_actions TEXT NOT NULL,
                first_action_seconds INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS follow_ups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                due_at TEXT NOT NULL,
                status TEXT NOT NULL,
                template TEXT NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                recipient TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
            );
            """
        )


def insert_lead(record: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO leads (
                id, created_at, full_name, email, phone, service_type,
                postal_code, message, preferred_contact, priority, score,
                reason, assigned_to, status, recommended_actions,
                first_action_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["created_at"],
                record["full_name"],
                record["email"],
                record["phone"],
                record["service_type"],
                record["postal_code"],
                record["message"],
                record["preferred_contact"],
                record["priority"],
                record["score"],
                record["reason"],
                record["assigned_to"],
                record["status"],
                json.dumps(record["recommended_actions"]),
                record["first_action_seconds"],
            ),
        )


def add_event(lead_id: str, event_type: str, description: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO events (lead_id, event_type, description, created_at) VALUES (?, ?, ?, ?)",
            (lead_id, event_type, description, now_iso()),
        )


def add_follow_up(lead_id: str, channel: str, due_at: str, template: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO follow_ups (lead_id, channel, due_at, status, template) VALUES (?, ?, ?, 'scheduled', ?)",
            (lead_id, channel, due_at, template),
        )


def add_notification(lead_id: str, channel: str, recipient: str, message: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO notifications (lead_id, channel, recipient, message, status, created_at) VALUES (?, ?, ?, ?, 'simulated', ?)",
            (lead_id, channel, recipient, message, now_iso()),
        )


def _decode_lead(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["recommended_actions"] = json.loads(result["recommended_actions"])
    return result


def list_leads(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_decode_lead(row) for row in rows]


def get_lead(lead_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not row:
            return None
        lead = _decode_lead(row)
        lead["events"] = [
            dict(item)
            for item in conn.execute(
                "SELECT event_type, description, created_at FROM events WHERE lead_id = ? ORDER BY id",
                (lead_id,),
            ).fetchall()
        ]
        lead["follow_ups"] = [
            dict(item)
            for item in conn.execute(
                "SELECT channel, due_at, status, template FROM follow_ups WHERE lead_id = ? ORDER BY id",
                (lead_id,),
            ).fetchall()
        ]
        lead["notifications"] = [
            dict(item)
            for item in conn.execute(
                "SELECT channel, recipient, message, status, created_at FROM notifications WHERE lead_id = ? ORDER BY id",
                (lead_id,),
            ).fetchall()
        ]
    return lead


def dashboard_stats() -> dict[str, Any]:
    with connect() as conn:
        counts = conn.execute(
            """
            SELECT
              COUNT(*) AS total,
              SUM(CASE WHEN priority = 'urgent' THEN 1 ELSE 0 END) AS urgent,
              SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) AS high,
              SUM(CASE WHEN priority = 'normal' THEN 1 ELSE 0 END) AS normal,
              COALESCE(AVG(first_action_seconds), 0) AS average_first_action_seconds
            FROM leads
            """
        ).fetchone()
        follow_ups = conn.execute(
            "SELECT COUNT(*) AS value FROM follow_ups WHERE status = 'scheduled'"
        ).fetchone()["value"]
        messages = conn.execute("SELECT COUNT(*) AS value FROM notifications").fetchone()["value"]

    return {
        "total": counts["total"] or 0,
        "urgent": counts["urgent"] or 0,
        "high": counts["high"] or 0,
        "normal": counts["normal"] or 0,
        "open_follow_ups": follow_ups,
        "simulated_messages": messages,
        "average_routing_target_seconds": round(counts["average_first_action_seconds"] or 0, 1),
    }


def lead_count() -> int:
    with connect() as conn:
        return conn.execute("SELECT COUNT(*) AS value FROM leads").fetchone()["value"]
