import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from functools import lru_cache
from typing import List

from app.config import get_settings

logger = logging.getLogger(__name__)


class SessionStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db(self):
        dir_path = os.path.dirname(self.db_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_messages (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role       TEXT NOT NULL,
                    content    TEXT NOT NULL,
                    agent_path TEXT,
                    sources    TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_session_id ON session_messages (session_id)"
            )
            conn.commit()
        logger.info(f"SessionStore 初始化完成，db_path={self.db_path}")

    def save_turn(
        self,
        session_id: str,
        query: str,
        answer: str,
        agent_path: list,
        sources: list,
    ):
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO session_messages (session_id, role, content, agent_path, sources, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, "user", query, None, None, now),
            )
            conn.execute(
                "INSERT INTO session_messages (session_id, role, content, agent_path, sources, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, "assistant", answer, json.dumps(agent_path, ensure_ascii=False), json.dumps(sources, ensure_ascii=False), now),
            )
            conn.commit()
        logger.info(f"save_turn 完成，session_id={session_id}")

    def get_history(self, session_id: str, limit: int = 10) -> List[dict]:
        # limit 指轮数，每轮 = user + assistant 两条记录
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT role, content, agent_path, sources, created_at"
                " FROM session_messages"
                " WHERE session_id = ?"
                " ORDER BY id ASC"
                " LIMIT ?",
                (session_id, limit * 2),
            ).fetchall()
        return [
            {
                "role": row["role"],
                "content": row["content"],
                "agent_path": json.loads(row["agent_path"]) if row["agent_path"] else [],
                "sources": json.loads(row["sources"]) if row["sources"] else [],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


@lru_cache(maxsize=1)
def get_session_store() -> SessionStore:
    settings = get_settings()
    return SessionStore(db_path=settings.SESSION_DB_PATH)
