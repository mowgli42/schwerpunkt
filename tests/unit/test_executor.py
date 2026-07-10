from schwerpunkt.act.executor import decide_with_risk, execute_action
from schwerpunkt.models import (
    CandidateAction,
    Decision,
    OrientationResult,
    Phase,
    RiskClass,
    SessionState,
    WorldModel,
)
from schwerpunkt.store import InMemoryStore


def _orientation(budget: float = 100, confidence: float = 0.9) -> OrientationResult:
    return OrientationResult(
        updated_model=WorldModel(risk_budget_remaining=budget),
        orientation_confidence=confidence,
    )


def test_decide_picks_highest_expected_value():
    candidates = [
        CandidateAction(id="A", name="a", expected_cost=1, expected_value=2),
        CandidateAction(id="B", name="b", expected_cost=2, expected_value=5),
        CandidateAction(id="C", name="c", expected_cost=0.5, expected_value=1),
    ]
    decision = decide_with_risk(_orientation(), candidates)
    assert decision.action and decision.action.id == "B"


def test_decide_honors_operator_chosen_candidate():
    candidates = [
        CandidateAction(id="A", name="a", expected_cost=1, expected_value=2),
        CandidateAction(id="C", name="c", expected_cost=0.5, expected_value=1),
    ]
    chosen = candidates[0]
    decision = decide_with_risk(_orientation(), candidates, chosen=chosen)
    assert decision.action and decision.action.id == "A"


def test_discrepancy_feeds_observe_phase():
    store = InMemoryStore()
    session = SessionState(id="d1", mode="stub", world_model=WorldModel(), phase=Phase.ACT)
    action = CandidateAction(
        id="X",
        name="force_discrepancy",
        expected_effects={"status": "ok"},
    )
    decision = Decision(action=action)
    session, result = execute_action(session, decision, store)
    assert result["verification_matches"] is False
    assert session.phase == Phase.OBSERVE
    assert session.observation and session.observation.pattern_id == "act_discrepancy_feedback"
    assert len(session.last_action.discrepancies) == 1