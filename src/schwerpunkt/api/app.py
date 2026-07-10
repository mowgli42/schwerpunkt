from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from schwerpunkt.models import Observation, Phase
from schwerpunkt.runtime.session import get_manager, reset_manager
from schwerpunkt.config import Settings, get_settings


class CreateSessionBody(BaseModel):
    objective: str = "Demo objective"
    scenario: str | None = "contradiction_case"
    risk_budget: float = 100.0


class ResolveBody(BaseModel):
    fact_key: str
    value: str
    rationale: str
    actor: str = "operator"


class DecideBody(BaseModel):
    candidate_id: str
    actor: str = "operator"


class ApproveBody(BaseModel):
    action_hash: str
    actor: str = "operator"


class LoadFixtureBody(BaseModel):
    scenario: str | None = None


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings:
        reset_manager(settings)
    app = FastAPI(title="Schwerpunkt Operator API", version="0.1.0")
    mgr = get_manager()
    static_dir = Path(__file__).resolve().parent / "static"

    @app.get("/health")
    def health() -> dict:
        s = settings or get_settings()
        return {"status": "ok", "mode": s.mode.value, "profile": s.profile.value}

    @app.post("/sessions")
    async def create_session(body: CreateSessionBody) -> dict:
        session = mgr.create_session(body.objective, body.scenario, body.risk_budget)
        return {"session_id": session.id, "mode": session.mode, "phase": session.phase.value}

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str) -> dict:
        session = mgr.get(session_id)
        if not session:
            raise HTTPException(404, "session not found")
        return session.model_dump()

    @app.post("/sessions/{session_id}/observe/fixture")
    def load_fixture(session_id: str, body: LoadFixtureBody) -> dict:
        try:
            session = mgr.load_observation(session_id, body.scenario)
        except KeyError:
            raise HTTPException(404, "session not found")
        return {"phase": session.phase.value, "observation": session.observation.model_dump() if session.observation else None}

    @app.post("/sessions/{session_id}/step")
    async def run_step(session_id: str) -> dict:
        try:
            session = await mgr.run_step(session_id)
        except KeyError:
            raise HTTPException(404, "session not found")
        return {
            "phase": session.phase.value,
            "pending_operator": session.pending_operator.model_dump() if session.pending_operator else None,
            "escalation": session.last_escalation.model_dump() if session.last_escalation else None,
        }

    @app.post("/sessions/{session_id}/resolve")
    def resolve(session_id: str, body: ResolveBody) -> dict:
        try:
            session = mgr.resolve_contradiction(session_id, body.fact_key, body.value, body.rationale, body.actor)
        except KeyError:
            raise HTTPException(404, "session not found")
        return {"phase": session.phase.value, "contradictions": [c.model_dump() for c in session.world_model.contradictions]}

    @app.post("/sessions/{session_id}/decide")
    def decide(session_id: str, body: DecideBody) -> dict:
        try:
            session = mgr.submit_decide(session_id, body.candidate_id, body.actor)
        except KeyError:
            raise HTTPException(404, "session not found")
        return {"phase": session.phase.value, "candidate_id": body.candidate_id}

    @app.post("/sessions/{session_id}/approve")
    def approve(session_id: str, body: ApproveBody) -> dict:
        try:
            token = mgr.approve(session_id, body.action_hash, body.actor)
        except KeyError:
            raise HTTPException(404, "session not found")
        return {"approval_token": token}

    @app.post("/sessions/{session_id}/checkpoint")
    def checkpoint(session_id: str) -> dict:
        try:
            session = mgr.acknowledge_checkpoint(session_id)
        except KeyError:
            raise HTTPException(404, "session not found")
        return {"phase": session.phase.value, "acknowledged": True}

    @app.post("/sessions/{session_id}/advance")
    async def advance(session_id: str) -> dict:
        try:
            session = await mgr.run_until_pause(session_id)
        except KeyError:
            raise HTTPException(404, "session not found")
        return {
            "phase": session.phase.value,
            "loop_count": session.world_model.loop_count,
            "pending_operator": session.pending_operator.model_dump() if session.pending_operator else None,
        }

    @app.get("/sessions/{session_id}/audit")
    def audit(session_id: str) -> dict:
        try:
            return mgr.audit_summary(session_id)
        except KeyError:
            raise HTTPException(404, "session not found")

    @app.get("/console", response_class=HTMLResponse)
    def console() -> HTMLResponse:
        html = (static_dir / "console.html").read_text()
        return HTMLResponse(html)

    return app


app = create_app()
