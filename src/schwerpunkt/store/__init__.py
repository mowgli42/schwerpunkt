from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Protocol

from schwerpunkt.models import AuditEvent, SessionState, WorldModel


class Store(Protocol):
    def save_session(self, session: SessionState) -> None: ...
    def load_session(self, session_id: str) -> SessionState | None: ...
    def append_audit(self, event: AuditEvent) -> None: ...
    def save_approval_token(self, session_id: str, action_hash: str, token: str) -> None: ...
    def consume_approval_token(self, session_id: str, action_hash: str, token: str) -> bool: ...


class InMemoryStore:
    def __init__(self) -> None:
        self.sessions: dict[str, SessionState] = {}
        self.audit: list[AuditEvent] = []
        self.tokens: dict[tuple[str, str, str], bool] = {}

    def save_session(self, session: SessionState) -> None:
        self.sessions[session.id] = session.model_copy(deep=True)

    def load_session(self, session_id: str) -> SessionState | None:
        s = self.sessions.get(session_id)
        return s.model_copy(deep=True) if s else None

    def append_audit(self, event: AuditEvent) -> None:
        self.audit.append(event)

    def save_approval_token(self, session_id: str, action_hash: str, token: str) -> None:
        self.tokens[(session_id, action_hash, token)] = True

    def consume_approval_token(self, session_id: str, action_hash: str, token: str) -> bool:
        key = (session_id, action_hash, token)
        if self.tokens.pop(key, None):
            return True
        return False


class SqliteStore:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                event_type TEXT,
                payload TEXT,
                actor TEXT,
                ts TEXT
            );
            CREATE TABLE IF NOT EXISTS approval_tokens (
                session_id TEXT,
                action_hash TEXT,
                token TEXT,
                consumed INTEGER DEFAULT 0,
                PRIMARY KEY (session_id, action_hash, token)
            );
            """
        )
        self.conn.commit()

    def save_session(self, session: SessionState) -> None:
        payload = session.model_dump_json()
        self.conn.execute(
            "INSERT OR REPLACE INTO sessions (id, payload) VALUES (?, ?)",
            (session.id, payload),
        )
        self.conn.commit()

    def load_session(self, session_id: str) -> SessionState | None:
        row = self.conn.execute("SELECT payload FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            return None
        return SessionState.model_validate_json(row[0])

    def append_audit(self, event: AuditEvent) -> None:
        self.conn.execute(
            "INSERT INTO audit_events (session_id, event_type, payload, actor, ts) VALUES (?, ?, ?, ?, ?)",
            (
                event.session_id,
                event.event_type,
                json.dumps(event.payload),
                event.actor,
                event.timestamp.isoformat(),
            ),
        )
        self.conn.commit()

    def save_approval_token(self, session_id: str, action_hash: str, token: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO approval_tokens (session_id, action_hash, token, consumed) VALUES (?, ?, ?, 0)",
            (session_id, action_hash, token),
        )
        self.conn.commit()

    def consume_approval_token(self, session_id: str, action_hash: str, token: str) -> bool:
        row = self.conn.execute(
            "SELECT consumed FROM approval_tokens WHERE session_id=? AND action_hash=? AND token=?",
            (session_id, action_hash, token),
        ).fetchone()
        if not row or row[0]:
            return False
        self.conn.execute(
            "UPDATE approval_tokens SET consumed=1 WHERE session_id=? AND action_hash=? AND token=?",
            (session_id, action_hash, token),
        )
        self.conn.commit()
        return True
