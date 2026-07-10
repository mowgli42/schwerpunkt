from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from schwerpunkt.models import (
    CandidateAction,
    Contradiction,
    Decision,
    Escalation,
    FactWithConfidence,
    Observation,
    OrientationResult,
    RiskClass,
    SessionState,
    WorldModel,
)
from schwerpunkt.orient.engine import merge_stub_orientation, orient_from_observation


class CognitionPort(Protocol):
    async def orient(
        self, session: SessionState, observation: Observation, world_model: WorldModel
    ) -> OrientationResult: ...

    async def decide(
        self, session: SessionState, orientation: OrientationResult
    ) -> Decision: ...


class StubCognition:
    def __init__(self, fixtures_dir: Path) -> None:
        self.fixtures_dir = fixtures_dir

    def _load(self, scenario: str, phase: str) -> dict:
        path = self.fixtures_dir / "cognition" / scenario / f"{phase}.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text())

    async def orient(
        self, session: SessionState, observation: Observation, world_model: WorldModel
    ) -> OrientationResult:
        scenario = session.scenario or "default"
        data = self._load(scenario, "orient")
        if data.get("force_contradiction"):
            from schwerpunkt.orient.engine import detect_contradictions

            contradictions = detect_contradictions(observation, world_model)
            if not contradictions and data.get("contradictions"):
                contradictions = [Contradiction(**c) for c in data["contradictions"]]
            return OrientationResult(
                updated_model=world_model.model_copy_update(contradictions=contradictions),
                contradictions=contradictions,
                requires_human_review=bool(contradictions),
                orientation_confidence=data.get("orientation_confidence", 0.4),
            )
        result = orient_from_observation(
            observation, world_model, data.get("confidence_factor", 1.0)
        )
        if "known_facts" in data:
            facts = {k: FactWithConfidence(**v) for k, v in data["known_facts"].items()}
            result = result.model_copy(
                update={"updated_model": merge_stub_orientation(result.updated_model, facts)}
            )
        if "orientation_confidence" in data:
            result.orientation_confidence = data["orientation_confidence"]
        return result

    async def decide(self, session: SessionState, orientation: OrientationResult) -> Decision:
        scenario = session.scenario or "default"
        data = self._load(scenario, "decide")
        if orientation.orientation_confidence < 0.3:
            return Decision(
                escalate=Escalation(reason="insufficient_orientation_confidence"),
                confidence=orientation.orientation_confidence,
            )
        if orientation.updated_model.risk_budget_remaining <= 0:
            return Decision(
                escalate=Escalation(reason="risk_budget_exhausted"),
                alternatives_considered=[
                    CandidateAction(**c) for c in data.get("candidates", [])
                ],
            )
        raw = data.get("candidates", [{"id": "A", "name": "default", "risk_class": "reversible", "expected_cost": 1}])
        candidates = [CandidateAction(**c) for c in raw]
        chosen_id = data.get("chosen_id", candidates[0].id)
        action = next((c for c in candidates if c.id == chosen_id), candidates[0])
        token = data.get("approval_token")
        if action.risk_class == RiskClass.IRREVERSIBLE and not token:
            return Decision(
                escalate=Escalation(reason="approval_required"),
                alternatives_considered=candidates,
            )
        return Decision(
            action=action,
            alternatives_considered=candidates,
            confidence=orientation.orientation_confidence,
            approval_token=token,
        )


class ManualCognition:
    """Orient/Decide delegated to SessionManager manual flow."""

    async def orient(
        self, session: SessionState, observation: Observation, world_model: WorldModel
    ) -> OrientationResult:
        return orient_from_observation(observation, world_model)

    async def decide(self, session: SessionState, orientation: OrientationResult) -> Decision:
        return Decision(escalate=Escalation(reason="manual_decide_pending"))


class LiveCognition:
    async def orient(
        self, session: SessionState, observation: Observation, world_model: WorldModel
    ) -> OrientationResult:
        raise NotImplementedError("LiveCognition requires LLM/MCP adapter (Phase 1D)")

    async def decide(self, session: SessionState, orientation: OrientationResult) -> Decision:
        raise NotImplementedError("LiveCognition requires LLM/MCP adapter (Phase 1D)")
