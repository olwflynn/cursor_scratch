import json
import os
import sqlite3
from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Tuple, Dict, Any


DATABASE_DIR = os.path.join(os.path.dirname(__file__), "data")
DATABASE_PATH = os.path.join(DATABASE_DIR, "garden.db")


# Note: Advice records are returned as dicts for consistency with other helpers.


def _ensure_db_dir() -> None:
    os.makedirs(DATABASE_DIR, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    _ensure_db_dir()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS advice (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                image_paths TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                embedding TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gardens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                elements TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        # New tables for garden elements, notes, and bloom events
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS elements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                location TEXT,
                planted_on TEXT,
                variety TEXT,
                image_path TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS element_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                element_id INTEGER NOT NULL,
                note_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (element_id) REFERENCES elements(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS element_blooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                element_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (element_id) REFERENCES elements(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def insert_advice(
    question_text: str,
    image_paths: Sequence[str],
    answer_text: str,
    embedding: Sequence[float],
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO advice (question_text, image_paths, answer_text, embedding, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                question_text,
                json.dumps(list(image_paths)),
                answer_text,
                json.dumps(list(embedding)),
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def _row_to_record(row: sqlite3.Row) -> dict:
    return {
        "id": int(row["id"]),
        "question_text": row["question_text"],
        "image_paths": json.loads(row["image_paths"]) if row["image_paths"] else [],
        "answer_text": row["answer_text"],
        "embedding": json.loads(row["embedding"]) if row["embedding"] else [],
        "created_at": row["created_at"],
    }


def fetch_recent(limit: int = 20) -> List[dict]:
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT * FROM advice ORDER BY datetime(created_at) DESC LIMIT ?",
            (limit,),
        )
        return [_row_to_record(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_advice_by_id(advice_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        cur = conn.execute("SELECT * FROM advice WHERE id = ?", (advice_id,))
        row = cur.fetchone()
        return _row_to_record(row) if row else None
    finally:
        conn.close()


def delete_advice(advice_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM advice WHERE id = ?", (advice_id,))
        conn.commit()
    finally:
        conn.close()


def insert_garden(name: str, elements: Sequence[dict]) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO gardens (name, elements, created_at)
            VALUES (?, ?, ?)
            """,
            (
                name,
                json.dumps(list(elements)),
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def fetch_gardens(limit: int = 20) -> List[dict]:
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT * FROM gardens ORDER BY datetime(created_at) DESC LIMIT ?",
            (limit,),
        )
        results = []
        for row in cur.fetchall():
            results.append({
                "id": int(row["id"]),
                "name": row["name"],
                "elements": json.loads(row["elements"]) if row["elements"] else [],
                "created_at": row["created_at"]
            })
        return results
    finally:
        conn.close()


def get_garden_by_id(garden_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        cur = conn.execute("SELECT * FROM gardens WHERE id = ?", (garden_id,))
        row = cur.fetchone()
        if row:
            return {
                "id": int(row["id"]),
                "name": row["name"],
                "elements": json.loads(row["elements"]) if row["elements"] else [],
                "created_at": row["created_at"]
            }
        return None
    finally:
        conn.close()


def delete_garden(garden_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM gardens WHERE id = ?", (garden_id,))
        conn.commit()
    finally:
        conn.close()


def search_text(query: str, limit: int = 20) -> List[dict]:
    pattern = f"%{query.strip()}%"
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT * FROM advice
            WHERE question_text LIKE ? OR answer_text LIKE ?
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            """,
            (pattern, pattern, limit),
        )
        return [_row_to_record(r) for r in cur.fetchall()]
    finally:
        conn.close()


def load_all_embeddings() -> List[Tuple[int, List[float]]]:
    conn = get_connection()
    try:
        cur = conn.execute("SELECT id, embedding FROM advice")
        rows = cur.fetchall()
        results: List[Tuple[int, List[float]]] = []
        for r in rows:
            emb = json.loads(r["embedding"]) if r["embedding"] else []
            results.append((int(r["id"]), emb))
        return results
    finally:
        conn.close()


def get_advice_by_ids(advice_ids: Iterable[int]) -> List[dict]:
    ids = list(advice_ids)
    if not ids:
        return []
    placeholders = ",".join(["?"] * len(ids))
    conn = get_connection()
    try:
        cur = conn.execute(
            f"SELECT * FROM advice WHERE id IN ({placeholders}) ORDER BY datetime(created_at) DESC",
            ids,
        )
        return [_row_to_record(r) for r in cur.fetchall()]
    finally:
        conn.close()


# -----------------------------
# Garden elements CRUD and logic
# -----------------------------

def create_element(
    name: str,
    type: str,
    location: Optional[str] = None,
    planted_on: Optional[str] = None,
    variety: Optional[str] = None,
    image_path: Optional[str] = None,
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO elements (name, type, location, planted_on, variety, image_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                type.strip(),
                (location or None),
                (planted_on or None),
                (variety or None),
                (image_path or None),
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def update_element(element_id: int, updates: Dict[str, Any]) -> None:
    if not updates:
        return
    fields = []
    values: List[Any] = []
    for k in ["name", "type", "location", "planted_on", "variety", "image_path"]:
        if k in updates:
            fields.append(f"{k} = ?")
            values.append(updates[k])
    if not fields:
        return
    values.append(element_id)
    conn = get_connection()
    try:
        conn.execute(f"UPDATE elements SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def delete_element(element_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM elements WHERE id = ?", (element_id,))
        conn.commit()
    finally:
        conn.close()


def get_element(element_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        cur = conn.execute("SELECT * FROM elements WHERE id = ?", (element_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": int(row["id"]),
            "name": row["name"],
            "type": row["type"],
            "location": row["location"],
            "planted_on": row["planted_on"],
            "variety": row["variety"],
            "image_path": row["image_path"],
            "created_at": row["created_at"],
        }
    finally:
        conn.close()


def list_elements(limit: int = 200) -> List[dict]:
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT * FROM elements ORDER BY datetime(created_at) DESC LIMIT ?",
            (limit,),
        )
        results: List[dict] = []
        for row in cur.fetchall():
            results.append({
                "id": int(row["id"]),
                "name": row["name"],
                "type": row["type"],
                "location": row["location"],
                "planted_on": row["planted_on"],
                "variety": row["variety"],
                "image_path": row["image_path"],
                "created_at": row["created_at"],
            })
        return results
    finally:
        conn.close()


def add_note(element_id: int, note_text: str) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO element_notes (element_id, note_text, created_at)
            VALUES (?, ?, ?)
            """,
            (
                element_id,
                note_text.strip(),
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_notes(element_id: int, limit: int = 200) -> List[dict]:
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT * FROM element_notes
            WHERE element_id = ?
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            """,
            (element_id, limit),
        )
        return [
            {
                "id": int(r["id"]),
                "element_id": int(r["element_id"]),
                "note_text": r["note_text"],
                "created_at": r["created_at"],
            }
            for r in cur.fetchall()
        ]
    finally:
        conn.close()


def add_bloom(element_id: int, start_date: str, end_date: Optional[str] = None) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO element_blooms (element_id, start_date, end_date, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                element_id,
                start_date,
                (end_date or None),
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_blooms(element_id: int, limit: int = 200) -> List[dict]:
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT * FROM element_blooms
            WHERE element_id = ?
            ORDER BY datetime(start_date) DESC, id DESC
            LIMIT ?
            """,
            (element_id, limit),
        )
        return [
            {
                "id": int(r["id"]),
                "element_id": int(r["element_id"]),
                "start_date": r["start_date"],
                "end_date": r["end_date"],
                "created_at": r["created_at"],
            }
            for r in cur.fetchall()
        ]
    finally:
        conn.close()


def compute_progress_stats() -> dict:
    """Aggregate simple stats for dashboard."""
    conn = get_connection()
    try:
        stats: Dict[str, Any] = {}
        # total elements and by type
        cur = conn.execute("SELECT COUNT(*) AS c FROM elements")
        stats["total_elements"] = int(cur.fetchone()["c"])
        cur = conn.execute("SELECT type, COUNT(*) AS c FROM elements GROUP BY type")
        stats["by_type"] = {row["type"]: int(row["c"]) for row in cur.fetchall()}
        # currently blooming = bloom with NULL end_date or end_date >= today
        cur = conn.execute(
            """
            SELECT COUNT(DISTINCT element_id) AS c
            FROM element_blooms
            WHERE (end_date IS NULL) OR (date(end_date) >= date('now'))
            """
        )
        stats["currently_blooming"] = int(cur.fetchone()["c"])
        # recent notes
        cur = conn.execute(
            "SELECT COUNT(*) AS c FROM element_notes WHERE datetime(created_at) >= datetime('now','-7 day')"
        )
        stats["notes_last_7_days"] = int(cur.fetchone()["c"])
        return stats
    finally:
        conn.close()


