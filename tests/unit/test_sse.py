import json

import pytest
from fastapi.testclient import TestClient

from schwerpunkt.api.app import create_app
from schwerpunkt.api.events import EscalationBus
from schwerpunkt.config import RunMode
from schwerpunkt.runtime.session import reset_manager


def _parse_sse_body(body: str) -> dict:
    for line in body.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    raise AssertionError("no SSE data event received")


def test_sse_escalation_includes_correlation_id(stub_settings):
    settings = stub_settings.model_copy(update={"mode": RunMode.MANUAL})
    client = TestClient(create_app(settings))

    r = client.post("/sessions", json={"objective": "demo", "scenario": "contradiction_case"})
    sid = r.json()["session_id"]
    client.post(f"/sessions/{sid}/observe/fixture", json={"scenario": "contradiction_case"})
    client.post(f"/sessions/{sid}/advance")

    resp = client.get(f"/sessions/{sid}/events", params={"snapshot_only": True})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    payload = _parse_sse_body(resp.text)
    assert payload["correlation_id"]
    assert payload["session_id"] == sid
    assert payload["pending_operator"]["kind"] == "orient"
    assert "world_model" in payload
    assert "contradictions" in payload["world_model"]


@pytest.mark.asyncio
async def test_escalation_bus_publish(stub_settings):
    settings = stub_settings.model_copy(update={"mode": RunMode.MANUAL})
    mgr = reset_manager(settings)
    bus = EscalationBus()

    session = mgr.create_session("bus test", "contradiction_case")
    mgr.load_observation(session.id, "contradiction_case")
    await mgr.run_step(session.id)

    payload = mgr.build_escalation_payload(session.id)
    assert payload
    queue = bus.subscribe(session.id)
    bus.publish(session.id, payload)
    received = queue.get_nowait()
    assert received["correlation_id"] == payload["correlation_id"]
