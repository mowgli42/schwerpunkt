from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from schwerpunkt.models import Observation, RiskClass, SessionState


class IGCRule(BaseModel):
    pattern_id: str
    min_observation_confidence: float = 0.8
    min_orientation_confidence: float = 0.8
    risk_class: RiskClass = RiskClass.REVERSIBLE
    action_name: str = "igc_action"


class IGCEngine:
    def __init__(self, rules_path: Path) -> None:
        self.rules: list[IGCRule] = []
        if rules_path.exists():
            data = json.loads(rules_path.read_text())
            self.rules = [IGCRule(**r) for r in data.get("rules", [])]

    def evaluate(
        self,
        session: SessionState,
        observation: Observation,
        orientation_confidence: float,
    ) -> IGCRule | None:
        if session.world_model.contradictions:
            return None
        pattern = observation.pattern_id
        if not pattern:
            return None
        for rule in self.rules:
            if rule.pattern_id != pattern:
                continue
            if rule.risk_class == RiskClass.IRREVERSIBLE:
                return None
            if observation.confidence < rule.min_observation_confidence:
                return None
            if orientation_confidence < rule.min_orientation_confidence:
                return None
            return rule
        return None
