from __future__ import annotations

from typing import TYPE_CHECKING

from schwerpunkt.models import (
    CandidateAction,
    Decision,
    Observation,
    OrientationResult,
    RiskClass,
    SessionState,
    Signal,
)

if TYPE_CHECKING:
    from schwerpunkt.store import Store


def decide_with_risk(
    orientation: OrientationResult,
    candidates: list[CandidateAction],
    approval_token: str | None = None,
    chosen: CandidateAction | None = None,
) -> Decision:
    from schwerpunkt.models import Escalation

    wm = orientation.updated_model
    if orientation.orientation_confidence < 0.3:
        return Decision(
            escalate=Escalation(reason="insufficient_orientation_confidence"),
            confidence=orientation.orientation_confidence,
        )
    if wm.risk_budget_remaining <= 0:
        return Decision(
            escalate=Escalation(reason="risk_budget_exhausted"),
            alternatives_considered=candidates,
        )
    viable: list[CandidateAction] = []
    for c in candidates:
        if c.risk_class == RiskClass.IRREVERSIBLE and not approval_token:
            continue
        if c.expected_cost <= wm.risk_budget_remaining:
            viable.append(c)
    if not viable:
        return Decision(
            escalate=Escalation(
                reason="no_viable_candidates",
                context={"candidates": [c.model_dump() for c in candidates]},
            ),
            alternatives_considered=candidates,
        )
    if chosen and chosen in viable:
        best = chosen
    else:
        best = max(viable, key=lambda x: x.expected_value)
    return Decision(
        action=best,
        alternatives_considered=candidates,
        confidence=orientation.orientation_confidence,
        approval_token=approval_token,
    )


def _verify_outcome(action: CandidateAction, outcome: dict) -> tuple[bool, list[Signal]]:
    if not action.expected_effects:
        return True, []
    discrepancies: list[Signal] = []
    for key, expected in action.expected_effects.items():
        actual = outcome.get(key)
        if actual != expected:
            discrepancies.append(
                Signal(key=key, value=actual, confidence=1.0, source="act_verification")
            )
    return len(discrepancies) == 0, discrepancies


def execute_action(
    session: SessionState,
    decision: Decision,
    store: Store | None = None,
) -> tuple[SessionState, dict]:
    from schwerpunkt.models import ActionResult, Phase

    if not decision.action:
        return session, {"skipped": True}

    action = decision.action
    token_consumed = False

    if action.risk_class == RiskClass.IRREVERSIBLE:
        from schwerpunkt.models import Escalation

        if not decision.approval_token or not action.action_hash:
            session.last_escalation = Escalation(reason="approval_required")
            session.phase = Phase.ESCALATED
            return session, {"blocked": True, "reason": "approval_required"}
        if store is None:
            return session, {"blocked": True, "reason": "no_store_for_token_consume"}
        if not store.consume_approval_token(session.id, action.action_hash, decision.approval_token):
            session.last_escalation = Escalation(reason="invalid_or_consumed_approval_token")
            session.phase = Phase.ESCALATED
            return session, {"blocked": True, "reason": "invalid_or_consumed_approval_token"}
        token_consumed = True
        session.operator_approval_token = None

    session.log(
        "intent",
        {
            "action": action.model_dump(),
            "igc_bypass": decision.igc_bypass,
            "action_hash": action.action_hash,
        },
    )
    cost = action.expected_cost
    wm = session.world_model.model_copy_update(
        risk_budget_remaining=max(0, session.world_model.risk_budget_remaining - cost),
        loop_count=session.world_model.loop_count + 1,
    )
    if action.risk_class == RiskClass.IRREVERSIBLE:
        taken = list(wm.irreversible_actions_taken)
        taken.append(action.name)
        wm = wm.model_copy_update(irreversible_actions_taken=taken)

    outcome: dict = {"action": action.name, **dict(action.expected_effects)}
    if action.name == "force_discrepancy":
        for key in action.expected_effects:
            outcome[key] = "unexpected"
    if action.name == "mark_complete":
        wm = wm.model_copy_update(objective_complete=True)
        outcome["objective_complete"] = True

    verified, discrepancies = _verify_outcome(action, outcome)
    session.world_model = wm
    result = ActionResult(
        success=True,
        risk_consumed=cost,
        outcome=outcome,
        verification_matches=verified,
        discrepancies=discrepancies,
    )
    session.last_action = result
    session.log(
        "outcome",
        {
            "result": result.model_dump(),
            "verified": result.verification_matches,
            "token_consumed": token_consumed,
        },
    )
    if decision.igc_bypass:
        session.log("igc_bypass", {"igc_rule_id": session.igc_rule_id})

    if discrepancies:
        session.observation = Observation(
            signals=discrepancies,
            confidence=0.9,
            pattern_id="act_discrepancy_feedback",
        )
        session.log("discrepancy_feedback", {"signals": [s.model_dump() for s in discrepancies]})
        session.phase = Phase.OBSERVE
    elif wm.objective_complete:
        session.phase = Phase.COMPLETE
    else:
        session.phase = Phase.OBSERVE

    return session, result.model_dump()
