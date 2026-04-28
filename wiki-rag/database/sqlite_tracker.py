import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "ingestion_tracker.db",
)


def _get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the ingested_entities table if it doesn't exist."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ingested_entities (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_name     TEXT UNIQUE,
                entity_type     TEXT,
                wikipedia_url   TEXT,
                chunk_count     INTEGER,
                ingested_at     TIMESTAMP,
                status          TEXT,
                error_message   TEXT
            )
        """)
        conn.commit()


def mark_ingested(
    entity_name: str,
    entity_type: str,
    url: str,
    chunk_count: int,
) -> None:
    with _get_connection() as conn:
        conn.execute("""
            INSERT INTO ingested_entities
                (entity_name, entity_type, wikipedia_url, chunk_count, ingested_at, status, error_message)
            VALUES (?, ?, ?, ?, ?, 'success', NULL)
            ON CONFLICT(entity_name) DO UPDATE SET
                entity_type   = excluded.entity_type,
                wikipedia_url = excluded.wikipedia_url,
                chunk_count   = excluded.chunk_count,
                ingested_at   = excluded.ingested_at,
                status        = 'success',
                error_message = NULL
        """, (entity_name, entity_type, url, chunk_count, datetime.utcnow()))
        conn.commit()


def mark_failed(
    entity_name: str,
    entity_type: str,
    error_message: str,
) -> None:
    with _get_connection() as conn:
        conn.execute("""
            INSERT INTO ingested_entities
                (entity_name, entity_type, wikipedia_url, chunk_count, ingested_at, status, error_message)
            VALUES (?, ?, NULL, 0, ?, 'failed', ?)
            ON CONFLICT(entity_name) DO UPDATE SET
                entity_type   = excluded.entity_type,
                ingested_at   = excluded.ingested_at,
                status        = 'failed',
                error_message = excluded.error_message
        """, (entity_name, entity_type, datetime.utcnow(), error_message))
        conn.commit()


def get_all_entities() -> list[dict]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM ingested_entities ORDER BY entity_type, entity_name"
        ).fetchall()
        return [dict(row) for row in rows]


def is_ingested(entity_name: str) -> bool:
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM ingested_entities WHERE entity_name = ?",
            (entity_name,),
        ).fetchone()
        return row is not None and row["status"] == "success"


def get_stats() -> dict:
    with _get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM ingested_entities").fetchone()[0]
        success = conn.execute(
            "SELECT COUNT(*) FROM ingested_entities WHERE status = 'success'"
        ).fetchone()[0]
        failed = conn.execute(
            "SELECT COUNT(*) FROM ingested_entities WHERE status = 'failed'"
        ).fetchone()[0]
        people_success = conn.execute(
            "SELECT COUNT(*) FROM ingested_entities WHERE entity_type = 'person' AND status = 'success'"
        ).fetchone()[0]
        places_success = conn.execute(
            "SELECT COUNT(*) FROM ingested_entities WHERE entity_type = 'place' AND status = 'success'"
        ).fetchone()[0]
        total_chunks = conn.execute(
            "SELECT COALESCE(SUM(chunk_count), 0) FROM ingested_entities WHERE status = 'success'"
        ).fetchone()[0]

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "people_success": people_success,
        "places_success": places_success,
        "total_chunks": total_chunks,
    }


def clear_all() -> None:
    with _get_connection() as conn:
        conn.execute("DELETE FROM ingested_entities")
        conn.commit()
