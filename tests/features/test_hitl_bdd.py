from __future__ import annotations

import pytest
from pytest_bdd import given, scenarios, then, when

from schwerpunkt.act.executor import decide_with_risk, execute_action
from schwerpunkt.models import (
    CandidateAction,
    Decision,
    FactWithConfidence,
    Observation,
    OrientationResult,
    Phase,
    RiskClass,
    SessionState,
    Signal,
    WorldModel,
)
from schwerpunkt.orient.engine import detect_contradictions, orient_from_observation, values_conflict
from schwerpunkt.store import InMemoryStore

scenarios("../../features/human-in-the-loop.feature")

_ctx: dict = {}


@pytest.fixture(autouse=True)
def clear_ctx():
    _ctx.clear()


@given("a world model with account_balance 1000")
def wm_balance():
    _ctx["wm"] = WorldModel(
        known_facts={
            "account_balance": FactWithConfidence(key="account_balance", value=1000, confidence=0.9)
        }
    )


@when("observation reports account_balance 1005")
def obs_balance():
    _ctx["obs"] = Observation(
        signals=[Signal(key="account_balance", value=1005, confidence=0.9, source="system")]
    )
    _ctx["contradictions"] = detect_contradictions(_ctx["obs"], _ctx["wm"])
    _ctx["result"] = orient_from_observation(_ctx["obs"], _ctx["wm"])


@then("no contradiction is raised")
def no_contradiction():
    assert not _ctx["contradictions"]
    assert not _ctx["result"].contradictions


@then("account_balance is revised to 1005")
def revised_balance():
    assert _ctx["result"].updated_model.known_facts["account_balance"].value == 1005


@given("a session with approval token for close_case")
def session_with_token():
    store = InMemoryStore()
    session = SessionState(
        id="tok1",
        mode="manual",
        world_model=WorldModel(task_objective="test", risk_budget_remaining=100),
        phase=Phase.ACT,
    )
    store.save_approval_token("tok1", "close_case", "abc123")
    action = CandidateAction(
        id="B",
        name="Close case",
        risk_class=RiskClass.IRREVERSIBLE,
        expected_cost=5,
        action_hash="close_case",
    )
    _ctx["store"] = store
    _ctx["session"] = session
    _ctx["decision"] = Decision(action=action, approval_token="abc123")


@when("Act executes close_case with the token")
def act_close():
    _ctx["session"], _ctx["outcome"] = execute_action(_ctx["session"], _ctx["decision"], _ctx["store"])


@then("the token is consumed")
def token_consumed():
    assert not _ctx["store"].consume_approval_token("tok1", "close_case", "abc123")


@then("audit records token_consumed true")
def audit_token():
    outcome_events = [e for e in _ctx["session"].audit if e.event_type == "outcome"]
    assert outcome_events
    assert outcome_events[-1].payload.get("token_consumed") is True


@given("a consumed approval token for close_case")
def consumed_token():
    store = InMemoryStore()
    session = SessionState(
        id="tok2",
        mode="manual",
        world_model=WorldModel(task_objective="test", risk_budget_remaining=100),
        phase=Phase.ACT,
    )
    store.save_approval_token("tok2", "close_case", "usedtok")
    store.consume_approval_token("tok2", "close_case", "usedtok")
    action = CandidateAction(
        id="B",
        name="Close case",
        risk_class=RiskClass.IRREVERSIBLE,
        expected_cost=5,
        action_hash="close_case",
    )
    _ctx["store"] = store
    _ctx["session"] = session
    _ctx["decision"] = Decision(action=action, approval_token="usedtok")


@when("Act attempts close_case again with the same token")
def act_reuse():
    _ctx["session"], _ctx["outcome"] = execute_action(_ctx["session"], _ctx["decision"], _ctx["store"])


@then("execution is blocked")
def blocked():
    assert _ctx["outcome"].get("blocked") is True


@then("escalation reason is invalid_or_consumed_approval_token")
def escalation_reason():
    assert _ctx["session"].last_escalation.reason == "invalid_or_consumed_approval_token"


@given("a high stakes session at loop count 10")
def high_stakes_session():
    from schwerpunkt.runtime.session import SessionManager
    from schwerpunkt.config import Settings, RunMode, Profile

    settings = Settings(mode=RunMode.MANUAL, profile=Profile.LOCAL)
    mgr = SessionManager(settings)
    s = mgr.create_session("hitl", "default")
    s.world_model = s.world_model.model_copy_update(high_stakes=True, loop_count=10, velocity_checkpoint_interval=10)
    s.observation = Observation(signals=[Signal(key="x", value=1)], confidence=0.95)
    s.phase = Phase.OBSERVE
    mgr.store.save_session(s)
    _ctx["manager"] = mgr
    _ctx["session_id"] = s.id


@when("Orient completes with sufficient confidence")
def orient_complete():
    import asyncio

    _ctx["session"] = asyncio.get_event_loop().run_until_complete(
        _ctx["manager"].run_step(_ctx["session_id"])
    )


@then("a velocity checkpoint pause is pending")
def velocity_pause():
    s = _ctx["session"]
    assert s.phase == Phase.PAUSED
    assert s.pending_operator and s.pending_operator.kind == "velocity_checkpoint"
