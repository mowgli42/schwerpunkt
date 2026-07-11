# Operator Interaction & Run Modes

Where humans touch the system, what runs locally, and how AI (MCP/API) stays **optional** for unit tests and manual operator demos.

## Design principle

> **Cognition is a plug-in, not a prerequisite.**

The OODA loop (observe → orient → decide → act), world model, contradiction detection, risk gating, and audit trail MUST run without any external LLM, MCP server, or cloud API. Live AI accelerates Orient and Decide in production; operators replace it in demo mode; stubs replace it in tests.

---

## Where users interact

| Surface | Actor | Phase(s) | Purpose |
|---------|-------|----------|---------|
| **Operator Console** (web) | Human operator | Orient, Decide, Act approval | Primary demo UI — step through loop, resolve contradictions, approve irreversible actions |
| **Operator API** (REST) | Console, scripts, integration tests | Same as console | Machine-readable human steps; console is a client |
| **CLI** (`schwerpunkt`) | Developer / operator | Session control, local demo | Start session, set mode, inject fixture observations, advance step |
| **Sensor feeds** (files, webhooks, in-proc) | System / test fixtures | Observe | Inject signals without AI |
| **MCP bridge** (optional) | External AI assistant (Cursor, etc.) | Orient, Decide (live only) | Exposes cognition tools to an LLM — **not used in test or manual demo** |
| **LLM API adapter** (optional) | Live cognition backend | Orient, Decide (live only) | Direct provider calls — **not used in test or manual demo** |

### Operator Console — demo flows

Operators manually perform the cognitive steps Boyd assigns to **Orientation** and **Decision**:

```
┌─────────────────────────────────────────────────────────────┐
│  Operator Console (manual / demo mode)                       │
├─────────────────────────────────────────────────────────────┤
│  [Observe]  Sensor panel — view signals, confidence, failures│
│  [Orient]   World model editor — facts, contradictions       │
│             Resolve conflict → human_resolved_facts          │
│  [Decide]   Candidate picker — select action OR escalate     │
│  [Act]      Approve irreversible → issues approval_token     │
│             Execute reversible → confirm outcome             │
│  [Audit]    Intent / outcome timeline per loop_count         │
└─────────────────────────────────────────────────────────────┘
```

### What operators do NOT need in demo mode

- API keys for OpenAI / Anthropic / etc.
- A running MCP server
- Network access (local profile uses SQLite + static fixtures)

---

## Run modes

Set via `SCHWERKPUNKT_MODE` (or `--mode` on CLI):

| Mode | Cognition backend | Store | Network | Use case |
|------|-------------------|-------|---------|----------|
| **`stub`** | `StubCognition` — fixture JSON / scripted responses | in-memory or temp SQLite | None | Unit tests, CI, pytest-bdd |
| **`manual`** | `ManualCognition` — blocks until operator submits via API/console | SQLite (local file) | Localhost only | Operator demo, training, dry-run |
| **`live`** | `LiveCognition` — LLM API and/or MCP tools | PostgreSQL (or SQLite dev) | Required | Production / AI-assisted ops |

### CognitionPort (shared interface)

All three modes implement the same port — the OODA runtime never imports LLM SDKs directly:

```python
class CognitionPort(Protocol):
    async def orient(self, observation: Observation, world_model: WorldModel) -> OrientationResult: ...
    async def decide(self, orientation: OrientationResult, world_model: WorldModel) -> Decision: ...
```

| Implementation | Orient / Decide behavior |
|----------------|--------------------------|
| `StubCognition` | Returns canned `OrientationResult` / `Decision` from `fixtures/cognition/` |
| `ManualCognition` | Publishes escalation to operator API; resumes when human POSTs resolution |
| `LiveCognition` | Calls LLM API adapter; may invoke MCP tools for retrieval |

**IG&C fast path** in `stub` and `manual` modes uses **rule tables** (pattern id → action), not LLM pattern matching.

---

## Local system demands

### Profile: `local` (test + demo)

| Component | Requirement |
|-----------|-------------|
| Python | 3.12+ |
| Database | SQLite file (`./data/schwerpunkt.db`) — no Postgres install |
| Processes | Single `uvicorn` (+ optional static console) |
| Memory | ~256 MB baseline (no embedding model loaded) |
| Disk | Fixtures + SQLite < 50 MB for demo |
| Network | **Off** for `stub` and `manual` |
| Secrets | None |

```bash
SCHWERKPUNKT_MODE=manual SCHWERKPUNKT_PROFILE=local uvicorn schwerpunkt.api:app
# Operator opens http://localhost:8000/console
```

### Profile: `server` (live / staging)

| Component | Requirement |
|-----------|-------------|
| PostgreSQL | 16+ (`PostgresStore` implemented; pgvector orientation memory deferred) |
| LLM API | Provider key via env (`OPENAI_API_KEY`, etc.) |
| MCP (optional) | Separate MCP server or in-process bridge |
| Network | Egress to LLM provider; ingress for operator API |

### Dependency injection at startup

```
SCHWERKPUNKT_MODE=stub|manual|live
SCHWERKPUNKT_PROFILE=local|server
→ CognitionPort factory
→ Store factory (SQLite vs Postgres)
→ Sensor registry (fixture vs live feeds)
```

Unit tests and demo scripts MUST only use `stub` + `local` or `manual` + `local`.

---

## Testing vs demo vs live

| Activity | Mode | Profile | External AI |
|----------|------|---------|-------------|
| `pytest tests/unit` | `stub` | in-memory | ❌ |
| `pytest tests/features` (BDD) | `stub` | SQLite temp | ❌ |
| Operator walkthrough | `manual` | `local` | ❌ |
| Conference / training demo | `manual` | `local` | ❌ |
| AI-assisted staging | `live` | `server` | ✅ API and/or MCP |
| Production | `live` | `server` | ✅ API and/or MCP |

---

## MCP vs API for live cognition

Both sit **behind** `LiveCognition` only:

| Approach | When to use | Trade-off |
|----------|-------------|-----------|
| **LLM API adapter** | Orient/Decide need direct model reasoning | Simple; no tool ecosystem |
| **MCP bridge** | Agent already runs in Cursor/IDE; tools are MCP-native | Extra process; great for dogfooding |
| **Both** | API for orientation updates; MCP for Observe tool calls | More flexible; more moving parts |

Neither is loaded when `SCHWERKPUNKT_MODE` is `stub` or `manual`.

---

## Related artifacts

- OpenSpec: `openspec/specs/runtime-modes/spec.md`, `openspec/specs/operator-console/spec.md`
- Architecture: [architecture.md](architecture.md)
- Beads: Phase 1 closed; Phase 2 live path (`schwerpunkt-i0i.2.10`); Phase 3 MTO/LGTM (`schwerpunkt-i0i.3`, gh-2/gh-3) — `bd list`
