from fastapi.testclient import TestClient

from schwerpunkt.api.app import create_app
from schwerpunkt.config import Profile, RunMode, Settings


def test_api_manual_flow(stub_settings):
    settings = stub_settings.model_copy(update={"mode": RunMode.MANUAL})
    client = TestClient(create_app(settings))

    r = client.post("/sessions", json={"objective": "demo", "scenario": "contradiction_case"})
    assert r.status_code == 200
    sid = r.json()["session_id"]

    r = client.post(f"/sessions/{sid}/observe/fixture", json={"scenario": "contradiction_case"})
    assert r.status_code == 200

    r = client.post(f"/sessions/{sid}/advance")
    assert r.status_code == 200
    assert r.json()["pending_operator"]["kind"] == "orient"

    r = client.post(
        f"/sessions/{sid}/resolve",
        json={"fact_key": "case_status", "value": "open", "rationale": "supervisor reopened"},
    )
    assert r.status_code == 200

    r = client.post(f"/sessions/{sid}/advance")
    body = r.json()
    assert body["phase"] in ("paused", "decide", "act", "observe")

    r = client.get("/console")
    assert r.status_code == 200
    html = r.text
    assert "Operator Console" in html
    assert "World model" in html
    assert "Contradictions" in html
    assert "known facts" in html
    assert "checkpointBanner" in html
    assert "EventSource" in html

    r = client.get("/health")
    assert r.json()["mode"] == "manual"
