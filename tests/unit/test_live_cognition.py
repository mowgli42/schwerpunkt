import json
import sys

import httpx
import pytest

from schwerpunkt.cognition.live import LiveCognition, create_live_cognition
from schwerpunkt.cognition.llm_client import LlmClient, MockLlmClient
from schwerpunkt.config import RunMode
from schwerpunkt.runtime.session import SessionManager, create_cognition


def test_stub_mode_does_not_import_live_module(stub_settings):
    if "schwerpunkt.cognition.live" in sys.modules:
        del sys.modules["schwerpunkt.cognition.live"]
    create_cognition(stub_settings)
    assert "schwerpunkt.cognition.live" not in sys.modules


@pytest.mark.asyncio
async def test_live_mode_mock_llm_completes_loop(stub_settings, monkeypatch):
    monkeypatch.setenv("SCHWERKPUNKT_LLM_MOCK", "1")
    settings = stub_settings.model_copy(update={"mode": RunMode.LIVE})
    mgr = SessionManager(settings)
    assert type(mgr.cognition).__name__ == "LiveCognition"
    assert isinstance(mgr.cognition.client, MockLlmClient)

    session = mgr.create_session("live-loop", "default")
    mgr.load_observation(session.id, "default")
    result = await mgr.run_full_stub(session.id)

    assert result.world_model.objective_complete
    assert result.world_model.loop_count >= 1
    assert result.phase.value in ("complete", "observe")


@pytest.mark.asyncio
async def test_llm_client_mock_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        user = json.loads(body["messages"][1]["content"])
        if user.get("phase") == "orient":
            content = json.dumps({"use_baseline": True, "orientation_confidence": 0.9})
        else:
            content = json.dumps({"chosen_id": "B"})
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": content}}]},
        )

    client = LlmClient(
        base_url="http://mock-llm",
        api_key="test",
        model="test-model",
        transport=httpx.MockTransport(handler),
    )
    orient = await client.complete_json("sys", json.dumps({"phase": "orient"}))
    decide = await client.complete_json("sys", json.dumps({"phase": "decide"}))
    assert orient["orientation_confidence"] == 0.9
    assert decide["chosen_id"] == "B"


@pytest.mark.asyncio
async def test_live_cognition_with_mock_transport(stub_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        user = json.loads(body["messages"][1]["content"])
        if user.get("phase") == "orient":
            payload = {"use_baseline": True, "orientation_confidence": 0.92}
        else:
            payload = {"chosen_id": user.get("default_chosen_id", "B")}
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(payload)}}]},
        )

    from pathlib import Path

    client = LlmClient(
        base_url="http://mock-llm",
        api_key="test",
        model="test-model",
        transport=httpx.MockTransport(handler),
    )
    cognition = LiveCognition(client, Path(stub_settings.fixtures_dir))
    settings = stub_settings.model_copy(update={"mode": RunMode.LIVE})
    mgr = SessionManager(settings)
    mgr.cognition = cognition

    session = mgr.create_session("live-http", "default")
    mgr.load_observation(session.id, "default")
    result = await mgr.run_full_stub(session.id)
    assert result.world_model.objective_complete
