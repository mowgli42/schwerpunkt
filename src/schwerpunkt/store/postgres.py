from __future__ import annotations

from typing import TYPE_CHECKING

from psycopg.types.json import Jsonb

from schwerpunkt.models import AuditEvent, SessionState

if TYPE_CHECKING:
    import psycopg


class PostgresStore:
    """PostgreSQL-backed store for SCHWERKPUNKT_PROFILE=server."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn
        self._init_schema()

    @classmethod
    def from_url(cls, database_url: str) -> PostgresStore:
        import psycopg

        return cls(psycopg.connect(database_url))

    def _init_schema(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    payload JSONB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload JSONB NOT NULL DEFAULT '{}',
                    actor TEXT NOT NULL DEFAULT 'system',
                    ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS approval_tokens (
                    session_id TEXT NOT NULL,
                    action_hash TEXT NOT NULL,
                    token TEXT NOT NULL,
                    consumed BOOLEAN NOT NULL DEFAULT FALSE,
                    PRIMARY KEY (session_id, action_hash, token)
                );
                """
            )
        self.conn.commit()

    def save_session(self, session: SessionState) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessions (id, payload) VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload
                """,
                (session.id, Jsonb(session.model_dump(mode="json"))),
            )
        self.conn.commit()

    def load_session(self, session_id: str) -> SessionState | None:
        with self.conn.cursor() as cur:
            cur.execute("SELECT payload FROM sessions WHERE id = %s", (session_id,))
            row = cur.fetchone()
        if not row:
            return None
        return SessionState.model_validate(row[0])

    def append_audit(self, event: AuditEvent) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit_events (session_id, event_type, payload, actor, ts)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    event.session_id,
                    event.event_type,
                    Jsonb(event.payload),
                    event.actor,
                    event.timestamp,
                ),
            )
        self.conn.commit()

    def save_approval_token(self, session_id: str, action_hash: str, token: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO approval_tokens (session_id, action_hash, token, consumed)
                VALUES (%s, %s, %s, FALSE)
                ON CONFLICT (session_id, action_hash, token)
                DO UPDATE SET consumed = FALSE
                """,
                (session_id, action_hash, token),
            )
        self.conn.commit()

    def consume_approval_token(self, session_id: str, action_hash: str, token: str) -> bool:
        with self.conn.transaction():
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT consumed FROM approval_tokens
                    WHERE session_id = %s AND action_hash = %s AND token = %s
                    FOR UPDATE
                    """,
                    (session_id, action_hash, token),
                )
                row = cur.fetchone()
                if not row or row[0]:
                    return False
                cur.execute(
                    """
                    UPDATE approval_tokens SET consumed = TRUE
                    WHERE session_id = %s AND action_hash = %s AND token = %s
                    """,
                    (session_id, action_hash, token),
                )
        return True

    def close(self) -> None:
        self.conn.close()
