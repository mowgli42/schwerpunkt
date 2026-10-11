# schwerpunkt

Orientation-first Boyd OODA loop runtime for AI agents: persistent WorldModel, contradiction detection, IG&C, operator console.
Stack: Python 3.12+ / FastAPI / SQLite (local) or PostgreSQL (server) / optional MCP + LLM.
Posture: ponytail (repo created 2026-07-10, >30 days).
Shared health pack lives in `.cursor/skills/` and `.cursor/rules/` — follow those for [Health] work.

## Commands

- Install: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
- Demo (headless): `make demo`
- Test (unit + Gherkin, no Docker): `make test` or `pytest tests/ -q -m "not integration"`
- Spec: `make spec` or `npx @fission-ai/openspec validate --specs --strict`
- Console: `SCHWERKPUNKT_MODE=manual SCHWERKPUNKT_PROFILE=local uvicorn schwerpunkt.api.app:app --reload` → http://127.0.0.1:8000/console
- Server profile: `docker compose up -d postgres && SCHWERKPUNKT_MODE=manual SCHWERKPUNKT_PROFILE=server uvicorn schwerpunkt.api.app:app`
- Secrets: `bash scripts/scan-secrets.sh .`
- Beads: `bd ready`

## Hard prohibitions

- Do not commit private keys, `*-key.pem`, `*.key`, `.env` secrets, or `BEGIN … PRIVATE KEY` blobs. Generate credentials locally; gitignore them. Public certs may stay.
- Do not invent CLI flags, env vars (`SCHWERKPUNKT_*`), API routes, or OpenSpec capabilities that are not already in this tree. Read `src/`, `openspec/`, and `docs/OPERATOR-AND-RUN-MODES.md` first.
- Do not rewrite OpenSpec or Gherkin to match a hoped-for Phase 3 (MTO/LGTM). Update them only when code already changed.
- Do not treat `.beads/issues.jsonl` as the source of truth. Use `bd` commands; the JSONL is a passive export.

## Verify by change type

| Change | Check |
| --- | --- |
| Runtime / Orient / WorldModel | `make test` + relevant unit or Gherkin |
| Operator API / console | `make test` + load http://127.0.0.1:8000/console and run contradiction_case |
| Spec | matching `.feature` + `make spec` still passes |
| Secrets / TLS | `bash scripts/scan-secrets.sh .` passes |
| Beads | `bd ready` shows expected next item |

## Source of truth

- Behavior: `openspec/specs/` + `features/*.feature`
- Remaining work: Beads (`bd ready`) + GitHub issues #2 (MTO) and #3 (LGTM)
- Demo evidence: `docs/screenshots/` + `docs/DEMO-WALKTHROUGH.md`
- Architecture: `docs/architecture.md` + README mermaid diagrams
- Health bar: do not duplicate `SUCCESS_CRITERIA.md` here

## House vocabulary

- Schwerpunkt — Orientation (persistent WorldModel), the center of gravity of the OODA loop. Do not write "context window" or "memory".
- IG&C — Implicit Guidance & Control; trained patterns that can bypass explicit Decide. Do not write "fast path" without naming IG&C.
- WorldModel — structured facts · contradictions · risk budget. Do not write "state" or "context".
- Manual mode — operator supplies Orient/Decide via console; no external AI. Do not invent a fourth mode.

## Good / bad (from this repo)

Bad: inventing a new `SCHWERKPUNKT_FOO` env var or FastAPI route that is not in `src/schwerpunkt/`.
Good: extending an existing cognition port (`StubCognition`, `ManualCognition`, `LiveCognition`) or store (`SQLite` / `PostgresStore`).

## Borrowed patterns

- Hard prohibitions from ossrules.md patterns (hard-prohibition) — secrets + no invented surface.
- Verification by change type from ossrules.md (verification-matrix) — maps runtime vs API vs spec.
- Pointing at the source of truth from ossrules.md (single-source) — OpenSpec / Beads / screenshots.
- House vocabulary from ossrules.md (house-vocabulary) — Schwerpunkt, IG&C, WorldModel.
