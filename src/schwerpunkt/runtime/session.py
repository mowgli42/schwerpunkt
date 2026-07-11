from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from schwerpunkt.act.executor import decide_with_risk, execute_action
from schwerpunkt.cognition import CognitionPort, ManualCognition, StubCognition
from schwerpunkt.config import Profile, RunMode, Settings, get_settings
from schwerpunkt.igc.engine import IGCEngine
from schwerpunkt.models import (
    CandidateAction,
    Decision,
    Escalation,
    HumanResolvedFact,
    Observation,
    Phase,
    RiskClass,
    SessionState,
    WorldModel,
)
from schwerpunkt.observe.fixtures import load_scenario_observation
from schwerpunkt.orient.engine import orient_from_observation
from schwerpunkt.store import InMemoryStore, PostgresStore, SqliteStore, Store


@dataclass
class ManualPending:
    orient_resolutions: list[dict] = field(default_factory=list)
    decide_candidate_id: str | None = None
    approval_token: str | None = None


def create_cognition(settings: Settings) -> CognitionPort:
    fixtures = Path(settings.fixtures_dir)
    if settings.mode == RunMode.STUB:
        return StubCognition(fixtures)
    if settings.mode == RunMode.MANUAL:
        return ManualCognition()
    from schwerpunkt.cognition.live import create_live_cognition

    return create_live_cognition(settings)


def create_store(settings: Settings) -> Store:
    import os

    if settings.mode == RunMode.STUB and settings.profile == Profile.LOCAL:
        if os.environ.get("SCHWERKPUNKT_USE_SQLITE") == "1":
            return SqliteStore(Path(settings.db_path))
        return InMemoryStore()
    if settings.profile == Profile.LOCAL:
        if settings.mode == RunMode.MANUAL or os.environ.get("SCHWERKPUNKT_USE_SQLITE") == "1":
            return SqliteStore(Path(settings.db_path))
        return InMemoryStore()
    return PostgresStore.from_url(settings.database_url)


class SessionManager:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.store = create_store(self.settings)
        self.cognition = create_cognition(self.settings)
        self.igc = IGCEngine(Path(self.settings.rules_path))
        self.manual: dict[str, ManualPending] = {}
        self.mcp_bridge = self._create_mcp_bridge()
        self._correlation_ids: dict[str, str] = {}

    def _create_mcp_bridge(self) -> Any | None:
        if self.settings.mode != RunMode.LIVE:
            return None
        from schwerpunkt.mcp.bridge import create_mcp_bridge

        return create_mcp_bridge(self.settings)

    def create_session(
        self,
        objective: str,
        scenario: str | None = None,
        risk_budget: float = 100.0,
        mode: str | None = None,
    ) -> SessionState:
        sid = str(uuid.uuid4())[:8]
        session = SessionState(
            id=sid,
            mode=mode or self.settings.mode.value,
            world_model=WorldModel(task_objective=objective, risk_budget_remaining=risk_budget),
            scenario=scenario,
        )
        self.manual[sid] = ManualPending()
        self._persist(session)
        return session

    def get(self, session_id: str) -> SessionState | None:
        session = self.store.load_session(session_id)
        if session and session_id not in self.manual:
            self.manual[session_id] = ManualPending()
        return session

    def _persist(self, session: SessionState) -> None:
        self.store.save_session(session)
        for ev in session.audit[-3:]:
            self.store.append_audit(ev)

    def build_escalation_payload(self, session_id: str) -> dict[str, Any] | None:
        session = self.get(session_id)
        if not session:
            return None
        if not session.pending_operator and not session.last_escalation:
            return None
        correlation_id = self._correlation_ids.get(session_id)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())[:12]
            self._correlation_ids[session_id] = correlation_id
        payload: dict[str, Any] = {
            "correlation_id": correlation_id,
            "session_id": session_id,
            "phase": session.phase.value,
            "world_model": session.world_model.model_dump(mode="json"),
        }
        if session.pending_operator:
            payload["pending_operator"] = session.pending_operator.model_dump(mode="json")
        if session.last_escalation:
            payload["escalation"] = session.last_escalation.model_dump(mode="json")
        return payload

    def _publish_operator_event(self, session: SessionState) -> None:
        if not session.pending_operator and not session.last_escalation:
            return
        from schwerpunkt.api.events import get_escalation_bus

        payload = self.build_escalation_payload(session.id)
        if payload:
            get_escalation_bus().publish(session.id, payload)

    async def load_observation_from_mcp(
        self,
        session_id: str,
        tool: str = "fetch_sensor",
        arguments: dict[str, Any] | None = None,
    ) -> SessionState:
        if not self.mcp_bridge:
            raise RuntimeError("MCP bridge is not enabled (live mode + mcp_enabled required)")
        from schwerpunkt.mcp.bridge import observation_from_mcp_result

        session = self._require(session_id)
        result = await self.mcp_bridge.call_tool(tool, arguments or {})
        observation = observation_from_mcp_result(result)
        session.observation = observation
        session.phase = Phase.OBSERVE
        session.log("observe_mcp", {"tool": tool, "arguments": arguments or {}})
        self._persist(session)
        return session

    def load_observation(self, session_id: str, scenario: str | None = None) -> SessionState:
        session = self._require(session_id)
        name = scenario or session.scenario or "default"
        session.scenario = name
        initial, obs = load_scenario_observation(Path(self.settings.fixtures_dir), name)
        if initial:
            facts = dict(session.world_model.known_facts)
            facts.update(initial)
            session.world_model = session.world_model.model_copy_update(known_facts=facts)
        session.observation = obs
        session.phase = Phase.OBSERVE
        session.log("observe", obs.model_dump(mode="json"))
        self._persist(session)
        return session

    def inject_observation(self, session_id: str, observation: Observation) -> SessionState:
        session = self._require(session_id)
        session.observation = observation
        session.log("observe", observation.model_dump())
        self._persist(session)
        return session

    def resolve_contradiction(
        self,
        session_id: str,
        fact_key: str,
        value: str,
        rationale: str,
        actor: str = "operator",
    ) -> SessionState:
        session = self._require(session_id)
        resolved = HumanResolvedFact(key=fact_key, value=value, rationale=rationale, actor=actor)
        wm = session.world_model.model_copy_update(
            human_resolved_facts=[*session.world_model.human_resolved_facts, resolved]
        )
        from schwerpunkt.orient.engine import apply_human_resolutions

        session.world_model = apply_human_resolutions(wm)
        session.pending_operator = None
        self._correlation_ids.pop(session_id, None)
        session.log("human_resolution", resolved.model_dump(), actor=actor)
        if session.observation:
            session.orientation = orient_from_observation(session.observation, session.world_model)
            session.world_model = session.orientation.updated_model
        session.phase = Phase.DECIDE
        self._persist(session)
        return session

    def submit_decide(self, session_id: str, candidate_id: str, actor: str = "operator") -> SessionState:
        session = self._require(session_id)
        session.operator_decide_id = candidate_id
        session.pending_operator = None
        self._correlation_ids.pop(session_id, None)
        session.phase = Phase.DECIDE
        session.log("operator_decide", {"candidate_id": candidate_id}, actor=actor)
        self._persist(session)
        return session

    def approve(self, session_id: str, action_hash: str, actor: str = "operator") -> str:
        import secrets

        session = self._require(session_id)
        token = secrets.token_hex(8)
        self.store.save_approval_token(session_id, action_hash, token)
        session.operator_approval_token = token
        session.pending_operator = None
        self._correlation_ids.pop(session_id, None)
        session.log("approval_token", {"action_hash": action_hash}, actor=actor)
        self._persist(session)
        return token

    def acknowledge_checkpoint(self, session_id: str, actor: str = "operator") -> SessionState:
        session = self._require(session_id)
        if not session.pending_operator or session.pending_operator.kind != "velocity_checkpoint":
            return session
        session.pending_operator = None
        self._correlation_ids.pop(session_id, None)
        session.phase = Phase.DECIDE
        session.log("velocity_checkpoint_ack", {"loop_count": session.world_model.loop_count}, actor=actor)
        self._persist(session)
        return session

    async def run_step(self, session_id: str) -> SessionState:
        session = self._require(session_id)
        if session.world_model.objective_complete:
            session.phase = Phase.COMPLETE
            self._persist(session)
            return session

        obs = session.observation
        if obs is None:
            session.phase = Phase.OBSERVE
            self._persist(session)
            return session

        if obs.confidence < 0.5 and len(obs.failed_sensors) >= 2:
            session.last_escalation = Escalation(
                reason="insufficient_observation_confidence",
                context={"failed_sensors": obs.failed_sensors},
            )
            session.phase = Phase.ESCALATED
            session.log("escalation", session.last_escalation.model_dump())
            self._publish_operator_event(session)
            self._persist(session)
            return session

        # Orient
        if session.phase in (Phase.OBSERVE, Phase.ORIENT):
            orientation = await self._orient(session, obs)
            session.orientation = orientation
            session.world_model = orientation.updated_model
            if orientation.requires_human_review and self.settings.mode == RunMode.MANUAL:
                session.phase = Phase.PAUSED
                self._publish_operator_event(session)
                self._persist(session)
                return session
            if orientation.orientation_confidence < 0.3:
                session.last_escalation = Escalation(reason="insufficient_orientation_confidence")
                session.phase = Phase.ESCALATED
                self._publish_operator_event(session)
                self._persist(session)
                return session

            # IG&C fast path: stub by default; manual only when SCHWERKPUNKT_IGC_MANUAL=1
            import os

            igc_manual = os.environ.get("SCHWERKPUNKT_IGC_MANUAL") == "1"
            igc_allowed = self.settings.mode == RunMode.STUB or (
                self.settings.mode == RunMode.MANUAL and igc_manual
            )
            rule = self.igc.evaluate(session, obs, orientation.orientation_confidence)
            if rule and igc_allowed and not session.world_model.high_stakes:
                decision = Decision(
                    action=CandidateAction(
                        id="igc",
                        name=rule.action_name,
                        risk_class=RiskClass.REVERSIBLE,
                        expected_cost=0.5,
                    ),
                    igc_bypass=True,
                    confidence=orientation.orientation_confidence,
                )
                session.igc_rule_id = rule.pattern_id
                session.decision = decision
                session, _ = execute_action(session, decision, self.store)
                self._persist(session)
                return session

            if self._velocity_checkpoint_required(session):
                from schwerpunkt.models import OperatorRequest

                session.pending_operator = OperatorRequest(
                    kind="velocity_checkpoint",
                    payload={"loop_count": session.world_model.loop_count},
                )
                session.phase = Phase.PAUSED
                self._publish_operator_event(session)
                self._persist(session)
                return session

            session.phase = Phase.DECIDE

        if session.phase == Phase.PAUSED:
            self._persist(session)
            return session

        # Decide
        if session.phase == Phase.DECIDE:
            decision = await self._decide(session)
            session.decision = decision
            if decision.escalate:
                session.last_escalation = decision.escalate
                session.phase = Phase.ESCALATED
                self._publish_operator_event(session)
                self._persist(session)
                return session
            if session.pending_operator and self.settings.mode == RunMode.MANUAL:
                session.phase = Phase.PAUSED
                self._publish_operator_event(session)
                self._persist(session)
                return session
            session.phase = Phase.ACT

        # Act
        if session.phase == Phase.ACT and session.decision:
            session, _ = execute_action(session, session.decision, self.store)
            self._persist(session)
            return session

        self._persist(session)
        return session

    async def run_until_pause(self, session_id: str, max_steps: int = 10) -> SessionState:
        for _ in range(max_steps):
            session = await self.run_step(session_id)
            if session.phase in (Phase.PAUSED, Phase.ESCALATED, Phase.COMPLETE):
                return session
            if session.last_action and session.last_action.success:
                return session
        return self._require(session_id)

    async def run_full_stub(self, session_id: str, max_steps: int = 10) -> SessionState:
        session = self.load_observation(session_id)
        for _ in range(max_steps):
            session = await self.run_step(session_id)
            if session.phase in (Phase.COMPLETE, Phase.ESCALATED):
                return session
        return session

    def audit_summary(self, session_id: str) -> dict:
        session = self._require(session_id)
        return {
            "session_id": session_id,
            "loop_count": session.world_model.loop_count,
            "phase": session.phase.value,
            "events": [e.model_dump() for e in session.audit],
        }

    async def _orient(self, session: SessionState, obs: Observation) -> OrientationResult:
        from schwerpunkt.models import OrientationResult

        if isinstance(self.cognition, ManualCognition):
            result = orient_from_observation(obs, session.world_model)
            if result.requires_human_review:
                from schwerpunkt.models import OperatorRequest

                session.pending_operator = OperatorRequest(
                    kind="orient",
                    payload={"contradictions": [c.model_dump() for c in result.contradictions]},
                )
                self._publish_operator_event(session)
            return result
        return await self.cognition.orient(session, obs, session.world_model)

    async def _decide(self, session: SessionState) -> Decision:
        orientation = session.orientation
        if not orientation:
            return Decision(escalate=Escalation(reason="missing_orientation"))

        if isinstance(self.cognition, ManualCognition):
            candidates = [
                CandidateAction(
                    id="A",
                    name="Investigate",
                    risk_class=RiskClass.REVERSIBLE,
                    expected_cost=1,
                    expected_value=3,
                ),
                CandidateAction(
                    id="B",
                    name="Close case",
                    risk_class=RiskClass.IRREVERSIBLE,
                    expected_cost=5,
                    expected_value=5,
                    action_hash="close_case",
                ),
                CandidateAction(
                    id="C",
                    name="Defer",
                    risk_class=RiskClass.REVERSIBLE,
                    expected_cost=0.5,
                    expected_value=1,
                ),
            ]
            if not session.operator_decide_id:
                from schwerpunkt.models import OperatorRequest

                session.pending_operator = OperatorRequest(
                    kind="decide",
                    payload={"candidates": [c.model_dump() for c in candidates]},
                )
                self._publish_operator_event(session)
                return Decision(alternatives_considered=candidates)
            chosen = next(c for c in candidates if c.id == session.operator_decide_id)
            token = session.operator_approval_token
            if chosen.risk_class == RiskClass.IRREVERSIBLE and not token:
                from schwerpunkt.models import OperatorRequest

                session.pending_operator = OperatorRequest(
                    kind="approve",
                    payload={"action_hash": chosen.action_hash, "candidate_id": chosen.id},
                )
                self._publish_operator_event(session)
                return Decision(alternatives_considered=candidates)
            session.operator_decide_id = None
            return decide_with_risk(orientation, candidates, token, chosen=chosen)

        if isinstance(self.cognition, StubCognition):
            return await self.cognition.decide(session, orientation)

        return await self.cognition.decide(session, orientation)

    def _require(self, session_id: str) -> SessionState:
        session = self.get(session_id)
        if not session:
            raise KeyError(f"session not found: {session_id}")
        return session

    def _velocity_checkpoint_required(self, session: SessionState) -> bool:
        wm = session.world_model
        if not wm.high_stakes:
            return False
        interval = wm.velocity_checkpoint_interval
        if interval <= 0:
            return False
        return wm.loop_count > 0 and wm.loop_count % interval == 0


# Singleton for API
_manager: SessionManager | None = None


def get_manager() -> SessionManager:
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager


def reset_manager(settings: Settings | None = None) -> SessionManager:
    global _manager
    _manager = SessionManager(settings)
    return _manager
