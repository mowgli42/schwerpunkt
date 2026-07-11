import pytest

from schwerpunkt.models import AuditEvent, Phase, SessionState, WorldModel
from schwerpunkt.store.postgres import PostgresStore


@pytest.fixture(scope="module")
def postgres_url():
    try:
        from testcontainers.postgres import PostgresContainer
    except ImportError:
        pytest.skip("testcontainers not installed")
    try:
        with PostgresContainer("postgres:16-alpine") as pg:
            yield pg.get_connection_url()
    except Exception as exc:
        pytest.skip(f"Docker not available for Postgres integration test: {exc}")


@pytest.mark.integration
def test_postgres_store_roundtrip(postgres_url: str):
    store = PostgresStore.from_url(postgres_url)
    try:
        session = SessionState(
            id="pg1",
            mode="manual",
            phase=Phase.OBSERVE,
            world_model=WorldModel(task_objective="postgres test", risk_budget_remaining=50),
        )
        session.log("observe", {"signals": []})
        store.save_session(session)

        loaded = store.load_session("pg1")
        assert loaded is not None
        assert loaded.id == "pg1"
        assert loaded.world_model.risk_budget_remaining == 50
        assert len(loaded.audit) == 1

        store.append_audit(
            AuditEvent(session_id="pg1", event_type="test", payload={"ok": True}, actor="pytest")
        )
        store.save_approval_token("pg1", "close_case", "tok123")
        assert store.consume_approval_token("pg1", "close_case", "tok123")
        assert not store.consume_approval_token("pg1", "close_case", "tok123")
    finally:
        store.close()


@pytest.mark.integration
def test_create_store_server_profile(postgres_url: str, monkeypatch):
    from schwerpunkt.config import Profile, RunMode, Settings
    from schwerpunkt.runtime.session import create_store

    settings = Settings(
        mode=RunMode.MANUAL,
        profile=Profile.SERVER,
        database_url=postgres_url,
    )
    store = create_store(settings)
    assert isinstance(store, PostgresStore)
    store.close()
