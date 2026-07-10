import pytest

from schwerpunkt.config import RunMode
from schwerpunkt.models import Phase
from schwerpunkt.runtime.session import SessionManager


@pytest.mark.asyncio
async def test_stub_mode_no_api_keys(stub_settings):
    mgr = SessionManager(stub_settings)
    assert stub_settings.mode == RunMode.STUB
    s = mgr.create_session("test", "default")
    s = mgr.load_observation(s.id, "default")
    s = await mgr.run_full_stub(s.id)
    assert s.world_model.loop_count >= 1


@pytest.mark.asyncio
async def test_igc_bypass_stub(manager):
    s = manager.create_session("igc", "igc_retrieve")
    manager.load_observation(s.id, "igc_retrieve")
    s = await manager.run_step(s.id)
    assert any(e.event_type == "igc_bypass" for e in s.audit) or s.decision and s.decision.igc_bypass


@pytest.mark.asyncio
async def test_risk_budget_exhausted(manager):
    s = manager.create_session("risk", "default", risk_budget=0)
    manager.load_observation(s.id, "default")
    s = await manager.run_step(s.id)
    s = await manager.run_step(s.id)
    assert s.last_escalation and s.last_escalation.reason == "risk_budget_exhausted"


@pytest.mark.asyncio
async def test_manual_pauses_on_contradiction(manual_manager):
    mgr = manual_manager
    s = mgr.create_session("manual", "contradiction_case")
    mgr.load_observation(s.id, "contradiction_case")
    s = await mgr.run_until_pause(s.id)
    assert s.phase == Phase.PAUSED
    assert s.pending_operator and s.pending_operator.kind == "orient"
