# Schwerpunkt

**Orientation-first OODA loop architecture for production AI agents.**

> *Schwerpunkt* (German: focal point) is John Boyd's term for **Orientation** — the center of gravity of the OODA loop. Agents that cycle fast with a miscalibrated orientation cycle fast toward the wrong answer. This repo captures the conceptual design, technology trade-offs, and spec-driven roadmap for building agents that treat orientation as a first-class, persistent world model — not a transient chain-of-thought.

**Source concept:** [Boyd OODA Loop Agility AI Insights (Grok)](https://grok.com/share/c2hhcmQtMg_431da025-0818-430c-90ee-b21f66bd5a56)

## Status

**Phase 2 complete — Live cognition, Postgres server profile, SSE, MCP (optional).**

Runnable stub/manual/live modes, operator console with SSE checkpoints, contradiction demo, and adversarial Gherkin coverage. LangGraph deferred. Phase 3 (MTO/LGTM) not started.

| Artifact | State |
|----------|-------|
| OpenSpec (7 capabilities) | Validated (`openspec validate --strict`) |
| Implementation | Python OODA runtime + SQLite / PostgreSQL + SSE + MCP mock |
| Demo | `contradiction_case` end-to-end (CLI + console) |
| Tests | 30+ passing (unit + Gherkin; integration with Docker) |
| Live LLM/MCP | LiveCognition + optional MCP bridge (`SCHWERKPUNKT_LLM_MOCK=1`, `SCHWERKPUNKT_MCP_MOCK=1`) |

## Maturity matrix (L0 → L3)

| Level | Name | Schwerpunkt today |
|-------|------|-------------------|
| **L0** | Specified | OpenSpec + Beads define full Boyd platform |
| **L1** | Implemented | Stub/manual runtime, IG&C rules, operator surfaces |
| **L2** | Verified | Partial — `human-in-the-loop.feature`, contradiction demo |
| **L3** | Production | Not started — auth, WORM audit, LangGraph |

**Honest scope:** The living specs describe a production-grade platform. The code is a **credible demo scaffold** with good bones. See [docs/GROK-FEEDBACK.md](docs/GROK-FEEDBACK.md) for adversarial review and prioritized gaps.

## What this is

| Layer | Purpose |
|-------|---------|
| **Concept** | Boyd OODA applied to agentic AI: Observe → Orient → Decide → Act with implicit guidance, contradiction detection, and human-in-the-loop gates |
| **OpenSpec** | Living Gherkin-style requirements in `openspec/specs/` |
| **Beads** | Epic/task breakdown in `.beads/` (`bd ready` for next work item) |
| **Runtime** | `src/schwerpunkt/` — session manager, orientation engine, operator API |
| **Docs** | Architecture, technology trade-offs, operator run modes, research briefs |

## Core insight (vs ReAct)

Most agent frameworks use a **ReAct** loop: reason → act → observe tool result → repeat. Boyd's OODA loop differs in three ways that matter for high-stakes agents:

1. **Orientation is persistent** — a structured world model, not ephemeral CoT
2. **Implicit Guidance & Control (IG&C)** — trained patterns can skip explicit Decide when confidence and risk allow
3. **Observation quality gates decisions** — low-confidence sensing triggers escalation, not blind action

## Run modes (no AI required for test & demo)

| Mode | Who does Orient/Decide | IG&C | External AI |
|------|------------------------|------|-------------|
| `stub` | Fixture JSON | Enabled | None — unit tests & CI |
| `manual` | **Operator** via console/API/CLI | Disabled by default | None — live demos |
| `live` | LLM API and/or MCP | TBD | `SCHWERKPUNKT_LLM_MOCK=1`, `SCHWERKPUNKT_MCP_MOCK=1` for tests |

```bash
SCHWERKPUNKT_MODE=manual SCHWERKPUNKT_PROFILE=local uvicorn schwerpunkt.api.app:app --reload
# Operator console: http://127.0.0.1:8000/console — no API keys needed
```

Set `SCHWERKPUNKT_IGC_MANUAL=1` to enable IG&C fast-path in manual mode (opt-in for demos).

**Live mode** (requires `pip install -e ".[server]"` for Postgres server profile):

```bash
export SCHWERKPUNKT_MODE=live
export SCHWERKPUNKT_LLM_MOCK=1          # tests/demos without API key
export SCHWERKPUNKT_MCP_MOCK=1          # MCP observe without MCP server
export SCHWERKPUNKT_MCP_ENABLED=1       # opt-in MCP bridge
# export SCHWERKPUNKT_LLM_API_KEY=...  # real provider
# export SCHWERKPUNKT_MCP_SERVER_URL=...  # real MCP HTTP endpoint
```

See [docs/OPERATOR-AND-RUN-MODES.md](docs/OPERATOR-AND-RUN-MODES.md) for interaction surfaces and local system demands.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

make demo          # headless contradiction_case demo (no AI)
make test          # unit + Gherkin
make spec          # OpenSpec strict validation

# Server profile (PostgreSQL)
docker compose up -d postgres
pip install -e ".[server,dev]"
SCHWERKPUNKT_MODE=manual SCHWERKPUNKT_PROFILE=server uvicorn schwerpunkt.api.app:app

# Browser operator console (local)
SCHWERKPUNKT_MODE=manual uvicorn schwerpunkt.api.app:app --reload
# → http://127.0.0.1:8000/console
```

### Console workflow

1. **New session** — creates `contradiction_case` and loads observe fixture
2. **Advance loop** — runs until a sensemaking checkpoint (contradiction, decide, approve, or velocity guard)
3. **World model panel** — facts, contradictions, risk budget, loop count
4. **Resolve / Decide / Approve** — operator actions per pending checkpoint
5. **Audit trail** — intent/outcome events for the session

See [docs/DEMO-WALKTHROUGH.md](docs/DEMO-WALKTHROUGH.md) for step-by-step instructions and **screenshot walkthrough**.

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/CONCEPT.md](docs/CONCEPT.md) | Full concept synthesis from Boyd + modern agent architecture research |
| [docs/OPERATOR-AND-RUN-MODES.md](docs/OPERATOR-AND-RUN-MODES.md) | Operator surfaces, local demands, stub/manual/live modes |
| [docs/DEMO-WALKTHROUGH.md](docs/DEMO-WALKTHROUGH.md) | Demo scripts and console walkthrough |
| [docs/GROK-FEEDBACK.md](docs/GROK-FEEDBACK.md) | Grok adversarial review response + Phase 2 scope |
| [docs/GROK-RESEARCH-BRIEF.md](docs/GROK-RESEARCH-BRIEF.md) | Spec vs implementation gap analysis |
| [docs/architecture.md](docs/architecture.md) | System architecture, data flows, domain objects |
| [docs/TECHNOLOGY-SELECTION.md](docs/TECHNOLOGY-SELECTION.md) | Technology options, trade-offs, recommended stack |
| [openspec/WORKFLOW.md](openspec/WORKFLOW.md) | Spec → Beads → implement → verify workflow |

## Living specs

| Capability | Spec | Gherkin |
|------------|------|---------|
| Index | [openspec/specs/README.md](openspec/specs/README.md) | — |
| OODA runtime | [ooda-runtime/spec.md](openspec/specs/ooda-runtime/spec.md) | partial |
| Orientation layer | [orientation-layer/spec.md](openspec/specs/orientation-layer/spec.md) | partial |
| Human-in-the-loop | [human-in-the-loop/spec.md](openspec/specs/human-in-the-loop/spec.md) | [features/human-in-the-loop.feature](features/human-in-the-loop.feature) |
| Runtime modes | [runtime-modes/spec.md](openspec/specs/runtime-modes/spec.md) | [features/runtime-modes.feature](features/runtime-modes.feature) |
| Operator console | [operator-console/spec.md](openspec/specs/operator-console/spec.md) | via API tests |
| Demo scenarios | [demo-scenarios/spec.md](openspec/specs/demo-scenarios/spec.md) | fixtures |

```bash
bd ready                    # next Beads task
npx @fission-ai/openspec validate --specs --strict
```

## Implemented vs backlog

| Area | Status |
|------|--------|
| Contradiction detection + human resolution | Done |
| Belief revision (numeric tolerance) | Done |
| Approval token consume at Act | Done |
| Act→Observe discrepancy feedback | Done |
| Velocity guard (high_stakes) | Done |
| Operator console (world model view) | Done |
| Postgres server profile | Done (`PostgresStore`, `docker-compose.yml`) |
| Live LLM / MCP adapters | Done — LiveCognition + optional MCP (`SCHWERKPUNKT_MCP_ENABLED=1`, mock env vars for CI) |
| MTO + impact integration | Phase 3 / [GitHub #2](https://github.com/mowgli42/schwerpunkt/issues/2) (`schwerpunkt-i0i.3.2`) |
| LGTM observability | Phase 3 / [GitHub #3](https://github.com/mowgli42/schwerpunkt/issues/3) (`schwerpunkt-i0i.3.3`) |
| LangGraph orchestration | Deferred (`schwerpunkt-i0i.2.10.4`) |
| SSE escalations | Done (`GET /sessions/{id}/events`, console EventSource) |

## License

MIT
