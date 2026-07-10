from __future__ import annotations

import asyncio
import json

import typer

from schwerpunkt.config import Profile, RunMode, Settings
from schwerpunkt.runtime.session import SessionManager

app = typer.Typer(help="Schwerpunkt OODA operator CLI")
session_app = typer.Typer(help="Session operations")
app.add_typer(session_app, name="session")


def _settings(mode: str, profile: str) -> Settings:
    return Settings(mode=RunMode(mode), profile=Profile(profile))


def _run(coro):
    return asyncio.run(coro)


@session_app.command("start")
def session_start(
    scenario: str = typer.Option("contradiction_case", "--scenario"),
    mode: str = typer.Option("manual", "--mode"),
    profile: str = typer.Option("local", "--profile"),
) -> None:
    mgr = SessionManager(_settings(mode, profile))
    s = mgr.create_session("CLI demo", scenario)
    typer.echo(json.dumps({"session_id": s.id}))


@session_app.command("load")
def session_load(
    session_id: str = typer.Option(..., "--id"),
    scenario: str = typer.Option("contradiction_case", "--scenario"),
    mode: str = typer.Option("manual", "--mode"),
    profile: str = typer.Option("local", "--profile"),
) -> None:
    mgr = SessionManager(_settings(mode, profile))
    s = mgr.load_observation(session_id, scenario)
    typer.echo(json.dumps({"phase": s.phase.value, "confidence": s.observation.confidence if s.observation else None}))


@session_app.command("run")
def session_run(
    session_id: str = typer.Option(..., "--id"),
    scenario: str = typer.Option(None, "--scenario"),
    mode: str = typer.Option("manual", "--mode"),
    profile: str = typer.Option("local", "--profile"),
) -> None:
    mgr = SessionManager(_settings(mode, profile))
    if scenario:
        mgr.load_observation(session_id, scenario)

    async def _go():
        return await mgr.run_until_pause(session_id)

    s = _run(_go())
    typer.echo(
        json.dumps(
            {
                "phase": s.phase.value,
                "pending": s.pending_operator.kind if s.pending_operator else None,
            }
        )
    )


@session_app.command("step")
def session_step(
    session_id: str = typer.Option(..., "--id"),
    mode: str = typer.Option("manual", "--mode"),
    profile: str = typer.Option("local", "--profile"),
) -> None:
    mgr = SessionManager(_settings(mode, profile))

    async def _go():
        return await mgr.run_step(session_id)

    s = _run(_go())
    typer.echo(json.dumps({"phase": s.phase.value, "pending": s.pending_operator.model_dump() if s.pending_operator else None}))


@session_app.command("resolve")
def session_resolve(
    session_id: str = typer.Option(..., "--id"),
    fact_key: str = typer.Option("case_status", "--fact-key"),
    value: str = typer.Option("open", "--value"),
    rationale: str = typer.Option("reopened by supervisor", "--rationale"),
    mode: str = typer.Option("manual", "--mode"),
    profile: str = typer.Option("local", "--profile"),
) -> None:
    mgr = SessionManager(_settings(mode, profile))
    s = mgr.resolve_contradiction(session_id, fact_key, value, rationale)
    typer.echo(json.dumps({"phase": s.phase.value}))


@session_app.command("decide")
def session_decide(
    session_id: str = typer.Option(..., "--id"),
    candidate: str = typer.Option("A", "--candidate"),
    mode: str = typer.Option("manual", "--mode"),
    profile: str = typer.Option("local", "--profile"),
) -> None:
    mgr = SessionManager(_settings(mode, profile))
    s = mgr.submit_decide(session_id, candidate)
    typer.echo(json.dumps({"phase": s.phase.value}))


@session_app.command("approve")
def session_approve(
    session_id: str = typer.Option(..., "--id"),
    action_hash: str = typer.Option("close_case", "--action-hash"),
    mode: str = typer.Option("manual", "--mode"),
    profile: str = typer.Option("local", "--profile"),
) -> None:
    mgr = SessionManager(_settings(mode, profile))
    token = mgr.approve(session_id, action_hash)
    typer.echo(json.dumps({"approval_token": token}))


if __name__ == "__main__":
    app()
