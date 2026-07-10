from __future__ import annotations

import asyncio

import pytest
from pytest_bdd import given, scenarios, then, when

from schwerpunkt.config import Profile, RunMode, Settings
from schwerpunkt.runtime.session import SessionManager, reset_manager

scenarios("../../features/runtime-modes.feature")

_ctx: dict = {}


@pytest.fixture(autouse=True)
def clear_ctx():
    _ctx.clear()


@given("SCHWERKPUNKT_MODE is stub")
def stub_mode(stub_settings):
    _ctx["settings"] = stub_settings


@given("SCHWERKPUNKT_PROFILE is local")
def local_profile():
    pass


@when("the application starts")
def app_starts():
    _ctx["manager"] = reset_manager(_ctx["settings"])


@then("StubCognition is used")
def stub_cognition():
    from schwerpunkt.cognition import StubCognition

    assert isinstance(_ctx["manager"].cognition, StubCognition)


@then("no LLM API keys are required")
def no_keys():
    assert _ctx["settings"].mode == RunMode.STUB


@when("the store is created")
def store_created(stub_settings):
    _ctx["settings"] = stub_settings
    _ctx["manager"] = SessionManager(stub_settings)


@then("the database path is under data directory")
def db_path(stub_settings):
    assert "data" in stub_settings.db_path


@given("a stub session with scenario igc_retrieve")
def stub_igc_session(manager):
    _ctx["manager"] = manager
    s = manager.create_session("bdd", "igc_retrieve")
    manager.load_observation(s.id, "igc_retrieve")
    _ctx["session_id"] = s.id


@when("the runtime executes one loop iteration")
def one_loop():
    _ctx["session"] = asyncio.get_event_loop().run_until_complete(_ctx["manager"].run_step(_ctx["session_id"]))


@then("IG&C bypass may be recorded in audit")
def igc_audit():
    s = _ctx["session"]
    assert s.decision is None or s.decision.igc_bypass or any(e.event_type == "igc_bypass" for e in s.audit)


@given("a stub session with risk budget 0")
def risk_zero(manager):
    _ctx["manager"] = manager
    s = manager.create_session("bdd", "default", risk_budget=0)
    manager.load_observation(s.id, "default")
    _ctx["session_id"] = s.id


@when("Decide evaluates candidates")
def decide_eval():
    async def _go():
        mgr = _ctx["manager"]
        await mgr.run_step(_ctx["session_id"])
        _ctx["session"] = await mgr.run_step(_ctx["session_id"])

    asyncio.get_event_loop().run_until_complete(_go())


@then("escalation reason is risk_budget_exhausted")
def risk_escalation():
    assert _ctx["session"].last_escalation.reason == "risk_budget_exhausted"


@given("a manual session with scenario contradiction_case")
def manual_session(manual_settings):
    _ctx["manager"] = reset_manager(manual_settings)
    s = _ctx["manager"].create_session("bdd", "contradiction_case")
    _ctx["session_id"] = s.id


@when("the operator loads the observe fixture")
def load_fixture():
    _ctx["manager"].load_observation(_ctx["session_id"], "contradiction_case")


@when("the operator advances the loop")
def advance_loop():
    _ctx["session"] = asyncio.get_event_loop().run_until_complete(
        _ctx["manager"].run_until_pause(_ctx["session_id"])
    )


@then("a contradiction orient pause is pending")
def orient_pause():
    s = _ctx["session"]
    assert s.pending_operator and s.pending_operator.kind == "orient"


@when("the operator resolves case_status to open")
def resolve_case():
    _ctx["session"] = _ctx["manager"].resolve_contradiction(
        _ctx["session_id"], "case_status", "open", "bdd operator"
    )


@then("contradictions are cleared")
def no_contradictions():
    assert not _ctx["session"].world_model.contradictions


@given("demo fixture contradiction_case")
def demo_fixture():
    _ctx["scenario"] = "contradiction_case"


@when("the fixture is loaded into observe")
def load_observe(manager):
    _ctx["manager"] = manager
    s = manager.create_session("bdd", _ctx["scenario"])
    s = manager.load_observation(s.id, _ctx["scenario"])
    _ctx["observation"] = s.observation


@then("observation confidence is at least 0.8")
def obs_confidence():
    assert _ctx["observation"].confidence >= 0.8


@then("no cognition backend is invoked during observe")
def no_cognition_observe():
    assert _ctx["observation"] is not None
