from __future__ import annotations

from schwerpunkt.models import (
    CandidateAction,
    Decision,
    OrientationResult,
    RiskClass,
    SessionState,
)


def decide_with_risk(
    orientation: OrientationResult,
    candidates: list[CandidateAction],
    approval_token: str | None = None,
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
    best = max(viable, key=lambda x: -x.expected_cost)
    return Decision(
        action=best,
        alternatives_considered=candidates,
        confidence=orientation.orientation_confidence,
        approval_token=approval_token,
    )


def execute_action(session: SessionState, decision: Decision) -> tuple[SessionState, dict]:
    from schwerpunkt.models import ActionResult, Phase

    if not decision.action:
        return session, {"skipped": True}
    session.log("intent", {"action": decision.action.model_dump(), "igc_bypass": decision.igc_bypass})
    cost = decision.action.expected_cost
    wm = session.world_model.model_copy_update(
        risk_budget_remaining=max(0, session.world_model.risk_budget_remaining - cost),
        loop_count=session.world_model.loop_count + 1,
    )
    if decision.action.risk_class == RiskClass.IRREVERSIBLE:
        taken = list(wm.irreversible_actions_taken)
        taken.append(decision.action.name)
        wm = wm.model_copy_update(irreversible_actions_taken=taken)
    if decision.action.name == "mark_complete":
        wm = wm.model_copy_update(objective_complete=True)
    session.world_model = wm
    result = ActionResult(success=True, risk_consumed=cost, outcome={"action": decision.action.name})
    session.last_action = result
    session.log(
        "outcome",
        {"result": result.model_dump(), "verified": result.verification_matches},
    )
    if decision.igc_bypass:
        session.log("igc_bypass", {"igc_rule_id": session.igc_rule_id})
    session.phase = Phase.COMPLETE if wm.objective_complete else Phase.OBSERVE
    return session, result.model_dump()
