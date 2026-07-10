from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Phase(str, Enum):
    OBSERVE = "observe"
    ORIENT = "orient"
    DECIDE = "decide"
    ACT = "act"
    PAUSED = "paused"
    COMPLETE = "complete"
    ESCALATED = "escalated"


class RiskClass(str, Enum):
    REVERSIBLE = "reversible"
    IRREVERSIBLE = "irreversible"


class Signal(BaseModel):
    key: str
    value: Any
    confidence: float = 1.0
    source: str = "sensor"

    def contradicts(self, other: FactWithConfidence) -> bool:
        if self.key != other.key:
            return False
        return self.value != other.value


class Observation(BaseModel):
    signals: list[Signal] = Field(default_factory=list)
    failed_sensors: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 1.0
    pattern_id: str | None = None


class FactWithConfidence(BaseModel):
    key: str
    value: Any
    confidence: float


class Contradiction(BaseModel):
    key: str
    new_value: Any
    prior_value: Any
    severity: LiteralSeverity = "high"
    prior_confidence: float


LiteralSeverity = str  # "high" | "low"


class HumanResolvedFact(BaseModel):
    key: str
    value: Any
    rationale: str
    actor: str = "operator"
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CandidateAction(BaseModel):
    id: str
    name: str
    risk_class: RiskClass = RiskClass.REVERSIBLE
    expected_cost: float = 1.0
    action_hash: str | None = None


class Escalation(BaseModel):
    reason: str
    context: dict[str, Any] = Field(default_factory=dict)


class Decision(BaseModel):
    action: CandidateAction | None = None
    escalate: Escalation | None = None
    alternatives_considered: list[CandidateAction] = Field(default_factory=list)
    confidence: float = 1.0
    igc_bypass: bool = False
    approval_token: str | None = None


class OrientationResult(BaseModel):
    updated_model: WorldModel
    contradictions: list[Contradiction] = Field(default_factory=list)
    requires_human_review: bool = False
    orientation_confidence: float = 1.0


class ActionResult(BaseModel):
    success: bool
    verification_matches: bool = True
    discrepancies: list[Signal] = Field(default_factory=list)
    risk_consumed: float = 0.0
    outcome: dict[str, Any] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    session_id: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str = "system"


class OperatorRequest(BaseModel):
    kind: LiteralOperatorKind
    payload: dict[str, Any] = Field(default_factory=dict)


LiteralOperatorKind = str  # orient | decide | approve


class WorldModel(BaseModel):
    task_objective: str = ""
    known_facts: dict[str, FactWithConfidence] = Field(default_factory=dict)
    contradictions: list[Contradiction] = Field(default_factory=list)
    human_resolved_facts: list[HumanResolvedFact] = Field(default_factory=list)
    irreversible_actions_taken: list[str] = Field(default_factory=list)
    risk_budget_remaining: float = 100.0
    loop_count: int = 0
    elapsed_ms: int = 0
    objective_complete: bool = False
    pending_hypotheses: list[str] = Field(default_factory=list)

    def model_copy_update(self, **kwargs: Any) -> WorldModel:
        return self.model_copy(update=kwargs)


class SessionState(BaseModel):
    id: str
    mode: str
    phase: Phase = Phase.OBSERVE
    world_model: WorldModel
    observation: Observation | None = None
    orientation: OrientationResult | None = None
    decision: Decision | None = None
    last_action: ActionResult | None = None
    scenario: str | None = None
    pending_operator: OperatorRequest | None = None
    last_escalation: Escalation | None = None
    operator_decide_id: str | None = None
    operator_approval_token: str | None = None
    audit: list[AuditEvent] = Field(default_factory=list)
    igc_rule_id: str | None = None

    def log(self, event_type: str, payload: dict[str, Any] | None = None, actor: str = "system") -> None:
        raw = payload or {}
        serializable = json.loads(json.dumps(raw, default=str))
        self.audit.append(
            AuditEvent(
                session_id=self.id,
                event_type=event_type,
                payload=serializable,
                actor=actor,
            )
        )
