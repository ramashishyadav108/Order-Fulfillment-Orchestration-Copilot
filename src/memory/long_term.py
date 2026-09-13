
from __future__ import annotations
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.models.memory import MemoryEntry, MemoryTier



class LongTermMemory:

    def __init__(self, db_path: str | Path):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    tier TEXT NOT NULL,
                    key TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    importance_score REAL DEFAULT 0.5,
                    session_id TEXT DEFAULT '',
                    order_id TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    ttl_hours INTEGER
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_order ON memories(order_id)
            """)
            conn.commit()

    def store(self, entry: MemoryEntry) -> None:
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO memories
                (memory_id, tier, key, content, metadata, importance_score,
                 session_id, order_id, created_at, last_accessed, access_count, ttl_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.memory_id,
                    entry.tier.value,
                    entry.key,
                    entry.content,
                    json.dumps(entry.metadata),
                    entry.importance_score,
                    entry.session_id,
                    entry.order_id,
                    entry.created_at.isoformat(),
                    entry.last_accessed.isoformat(),
                    entry.access_count,
                    entry.ttl_hours,
                ),
            )
            conn.commit()
        print("Stored memory: %s (key=%s)", entry.memory_id, entry.key)

    def recall(self, key: str) -> Optional[MemoryEntry]:
        with sqlite3.connect(str(self._db_path)) as conn:
            row = conn.execute(
                "SELECT * FROM memories WHERE key = ? ORDER BY created_at DESC LIMIT 1",
                (key,),
            ).fetchone()

            if row:
                entry = self._row_to_entry(row)
                # Update access metadata
                conn.execute(
                    "UPDATE memories SET last_accessed = ?, access_count = access_count + 1 WHERE memory_id = ?",
                    (datetime.utcnow().isoformat(), entry.memory_id),
                )
                conn.commit()
                return entry
        return None

    def recall_by_session(self, session_id: str) -> List[MemoryEntry]:
        with sqlite3.connect(str(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM memories WHERE session_id = ? ORDER BY created_at DESC",
                (session_id,),
            ).fetchall()
            return [self._row_to_entry(row) for row in rows]

    def recall_by_order(self, order_id: str) -> List[MemoryEntry]:
        with sqlite3.connect(str(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM memories WHERE order_id = ? ORDER BY created_at DESC",
                (order_id,),
            ).fetchall()
            return [self._row_to_entry(row) for row in rows]

    def search(self, keyword: str, limit: int = 10) -> List[MemoryEntry]:
        with sqlite3.connect(str(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM memories WHERE key LIKE ? OR content LIKE ? ORDER BY importance_score DESC LIMIT ?",
                (f"%{keyword}%", f"%{keyword}%", limit),
            ).fetchall()
            return [self._row_to_entry(row) for row in rows]

    def get_all(self, limit: int = 100) -> List[MemoryEntry]:
        with sqlite3.connect(str(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY importance_score DESC, created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [self._row_to_entry(row) for row in rows]

    def delete(self, memory_id: str) -> bool:
        with sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.execute("DELETE FROM memories WHERE memory_id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0

    def count(self) -> int:
        with sqlite3.connect(str(self._db_path)) as conn:
            row = conn.execute("SELECT COUNT(*) FROM memories").fetchone()
            return row[0] if row else 0

    def clear(self) -> None:
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("DELETE FROM memories")
            conn.commit()
        print("Long-term memory cleared")

    def _row_to_entry(self, row: tuple) -> MemoryEntry:
        return MemoryEntry(
            memory_id=row[0],
            tier=MemoryTier(row[1]),
            key=row[2],
            content=row[3],
            metadata=json.loads(row[4]) if row[4] else {},
            importance_score=row[5],
            session_id=row[6],
            order_id=row[7],
            created_at=datetime.fromisoformat(row[8]),
            last_accessed=datetime.fromisoformat(row[9]),
            access_count=row[10],
            ttl_hours=row[11],
        )
