import pytest
from fastapi.testclient import TestClient

from schwerpunkt.api.app import create_app
from schwerpunkt.config import RunMode
from schwerpunkt.runtime.session import reset_manager


def test_mcp_observe_mock_live_mode(stub_settings, monkeypatch):
    monkeypatch.setenv("SCHWERKPUNKT_MCP_MOCK", "1")
    monkeypatch.setenv("SCHWERKPUNKT_LLM_MOCK", "1")
    settings = stub_settings.model_copy(update={"mode": RunMode.LIVE, "mcp_enabled": True})
    client = TestClient(create_app(settings))

    r = client.post("/sessions", json={"objective": "mcp demo"})
    sid = r.json()["session_id"]
    r = client.post(
        f"/sessions/{sid}/observe/mcp",
        json={"tool": "fetch_sensor", "arguments": {"scenario": "contradiction_case"}},
    )
    assert r.status_code == 200
    obs = r.json()["observation"]
    assert obs["signals"][0]["key"] == "case_status"
    assert obs["pattern_id"] == "mcp"


def test_mcp_disabled_returns_400(stub_settings):
    settings = stub_settings.model_copy(update={"mode": RunMode.STUB, "mcp_enabled": False})
    client = TestClient(create_app(settings))

    r = client.post("/sessions", json={"objective": "demo"})
    sid = r.json()["session_id"]
    r = client.post(f"/sessions/{sid}/observe/mcp", json={})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_load_observation_from_mcp_unit(stub_settings, monkeypatch):
    monkeypatch.setenv("SCHWERKPUNKT_MCP_MOCK", "1")
    settings = stub_settings.model_copy(update={"mode": RunMode.LIVE, "mcp_enabled": True})
    mgr = reset_manager(settings)

    session = mgr.create_session("mcp unit test")
    result = await mgr.load_observation_from_mcp(session.id, "fetch_sensor", {"scenario": "default"})
    assert result.observation
    assert result.observation.signals[0].source == "mcp_mock"
