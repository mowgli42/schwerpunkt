from __future__ import annotations

import json
import os
from pathlib import Path

from schwerpunkt.act.executor import decide_with_risk
from schwerpunkt.cognition.llm_client import LlmClient, LlmClientProtocol, MockLlmClient
from schwerpunkt.config import Settings
from schwerpunkt.models import (
    CandidateAction,
    Decision,
    Escalation,
    Observation,
    OrientationResult,
    RiskClass,
    SessionState,
    WorldModel,
)
from schwerpunkt.orient.engine import orient_from_observation


ORIENT_SYSTEM = (
    "You assist Boyd OODA Orientation (schwerpunkt). "
    "Respond with JSON only. Prefer use_baseline=true to merge sensor fusion from the runtime."
)
DECIDE_SYSTEM = (
    "You assist Boyd OODA Decide. Pick one candidate id from the provided list. Respond with JSON: "
    '{"chosen_id": "<id>"}'
)


def create_live_cognition(settings: Settings) -> LiveCognition:
    fixtures = Path(settings.fixtures_dir)
    if os.environ.get("SCHWERKPUNKT_LLM_MOCK") == "1":
        client: LlmClientProtocol = MockLlmClient()
    else:
        client = LlmClient.from_settings(settings)
    return LiveCognition(client, fixtures)


class LiveCognition:
    """LLM-backed cognition for SCHWERKPUNKT_MODE=live only."""

    def __init__(self, client: LlmClientProtocol, fixtures_dir: Path) -> None:
        self.client = client
        self.fixtures_dir = fixtures_dir

    def _load_decide_fixture(self, scenario: str) -> dict:
        path = self.fixtures_dir / "cognition" / scenario / "decide.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text())

    async def orient(
        self, session: SessionState, observation: Observation, world_model: WorldModel
    ) -> OrientationResult:
        baseline = orient_from_observation(observation, world_model)
        scenario = session.scenario or "default"
        prompt = json.dumps(
            {
                "phase": "orient",
                "scenario": scenario,
                "task_objective": world_model.task_objective,
                "signals": [s.model_dump() for s in observation.signals],
                "known_facts": {k: v.model_dump() for k, v in world_model.known_facts.items()},
                "baseline_confidence": baseline.orientation_confidence,
                "baseline_requires_human_review": baseline.requires_human_review,
            }
        )
        llm = await self.client.complete_json(ORIENT_SYSTEM, prompt)
        if llm.get("use_baseline", True):
            confidence = float(llm.get("orientation_confidence", baseline.orientation_confidence))
            requires_review = bool(llm.get("requires_human_review", baseline.requires_human_review))
            return baseline.model_copy(
                update={
                    "orientation_confidence": confidence,
                    "requires_human_review": requires_review,
                }
            )
        return baseline

    async def decide(self, session: SessionState, orientation: OrientationResult) -> Decision:
        if orientation.orientation_confidence < 0.3:
            return Decision(
                escalate=Escalation(reason="insufficient_orientation_confidence"),
                confidence=orientation.orientation_confidence,
            )
        if orientation.updated_model.risk_budget_remaining <= 0:
            return Decision(
                escalate=Escalation(reason="risk_budget_exhausted"),
            )

        scenario = session.scenario or "default"
        data = self._load_decide_fixture(scenario)
        raw = data.get(
            "candidates",
            [
                {"id": "A", "name": "Investigate", "risk_class": "reversible", "expected_cost": 1, "expected_value": 2},
                {"id": "B", "name": "mark_complete", "risk_class": "reversible", "expected_cost": 1, "expected_value": 3},
            ],
        )
        candidates = [CandidateAction(**c) for c in raw]
        default_chosen = data.get("chosen_id", candidates[0].id)

        prompt = json.dumps(
            {
                "phase": "decide",
                "scenario": scenario,
                "task_objective": orientation.updated_model.task_objective,
                "orientation_confidence": orientation.orientation_confidence,
                "candidates": [c.model_dump() for c in candidates],
                "default_chosen_id": default_chosen,
            }
        )
        llm = await self.client.complete_json(DECIDE_SYSTEM, prompt)
        chosen_id = llm.get("chosen_id", default_chosen)
        chosen = next((c for c in candidates if c.id == chosen_id), candidates[0])
        return decide_with_risk(orientation, candidates, chosen=chosen)
