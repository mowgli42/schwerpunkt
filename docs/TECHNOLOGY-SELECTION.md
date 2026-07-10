# Technology Selection — Schwerpunkt OODA Agent Platform

This document evaluates implementation options for the Schwerpunkt conceptual architecture, records trade-offs, and documents the **selected stack** for Phase 1. It is the authoritative ADR for technology choices until superseded by an OpenSpec change.

**Decision date:** 2026-07-09  
**Status:** Accepted (concept phase)

---

## Decision summary

| Layer | **Selected** | Alternatives considered |
|-------|--------------|-------------------------|
| Language / runtime | **Python 3.12+** | TypeScript, Rust |
| Agent orchestration | **LangGraph** | Custom asyncio, Temporal, CrewAI |
| LLM integration | **LangChain + provider adapters** | Raw SDK, Vercel AI SDK |
| Orientation / memory store | **PostgreSQL 16 + pgvector** | Redis, Qdrant-only, graph DB |
| Event / audit log | **PostgreSQL append-only table** | Kafka, JSONL files |
| API | **FastAPI** | Starlette bare, gRPC |
| Human-in-the-loop | **LangGraph interrupts + FastAPI SSE** | Custom webhook, Temporal signals |
| Observability | **OpenTelemetry + structured logs** | LangSmith-only, Datadog-only |
| Testing | **pytest + pytest-bdd (Gherkin)** — stub mode in CI, no LLM/MCP | Vitest (if TS stack) |

---

## 1. Orchestration model

The core architectural fork is whether OODA phases are **explicit first-class nodes** or an **implicit ReAct loop with labels**.

### Option A: LangGraph state machine (selected)

**Description:** Each OODA phase is a graph node; world model lives in typed state; `interrupt_before` enables human checkpoints; checkpoints persist to Postgres.

| Pros | Cons |
|------|------|
| Native fit for Observe→Orient→Decide→Act with conditional IG&C edges | Python-centric; team must know LangGraph mental model |
| Built-in persistence and human-in-the-loop interrupts | Graph complexity grows; needs discipline |
| Active ecosystem, LangChain tool integration | Vendor coupling to LangChain stack |
| Checkpoint/resume aligns with escalation flows | |

### Option B: Custom asyncio loop

**Description:** Hand-rolled `OODARuntime` with async phase classes (as in production OODA articles).

| Pros | Cons |
|------|------|
| Zero framework magic; full control | Reinvent checkpointing, HITL, retries |
| Easy to unit-test each phase in isolation | Operational maturity takes months |
| Minimal dependencies | No standard graph visualization |

### Option C: Temporal workflows

**Description:** Each loop iteration or phase as durable workflow activities.

| Pros | Cons |
|------|------|
| Excellent durability and long-running human waits | Heavy ops footprint (Temporal cluster) |
| Strong audit trail via workflow history | Awkward for sub-second IG&C fast paths |
| Great for enterprise IT that already runs Temporal | Overkill for Phase 1 prototype |

### Option D: CrewAI / role-based multi-agent

**Description:** Separate "Observer", "Orienteer", "Planner", "Executor" agents.

| Pros | Cons |
|------|------|
| Mirrors OODA metaphor in org chart | **Fragments orientation** — Boyd's schwerpunkt is one world model, not four siloed agents |
| Good for demos | Contradiction consistency across agents is hard |
| | Higher token cost, slower cycles |

**Selection rationale:** LangGraph gives explicit phase boundaries and HITL without Temporal's weight. Custom asyncio is a credible Phase 2 refactor *inside* LangGraph nodes if we need tighter control. CrewAI is rejected because orientation must be unified.

---

## 2. Language runtime

### Option A: Python 3.12+ (selected)

| Pros | Cons |
|------|------|
| LangGraph/LangChain first-class | GIL limits CPU-bound sensor parallelism (mitigate with async I/O) |
| Dominant ML/agent hiring pool | Type safety weaker than TypeScript/Rust without discipline |
| FastAPI + asyncio for parallel Observe | |
| pytest-bdd for OpenSpec Gherkin | |

### Option B: TypeScript (Node/Bun)

| Pros | Cons |
|------|------|
| Vercel AI SDK, strong typing | LangGraph.js less mature than Python at time of writing |
| Same language as many web UIs | Enterprise agent patterns more documented in Python |
| Excellent for SSE/WebSocket API colocated with Svelte/React | |

### Option C: Rust

| Pros | Cons |
|------|------|
| Performance, safety | Slowest path to LangGraph-equivalent orchestration |
| Great for sensor adapters at edge | LLM ecosystem friction for orientation updates |
| | Team velocity risk for conceptual phase |

**Selection rationale:** Python maximizes velocity for a **concept → spec → prototype** repo where orchestration and HITL matter more than raw throughput. TypeScript remains the recommendation for a **dedicated operator console UI** (Phase 2) calling the Python API.

---

## 3. Orientation / world model storage

Orientation must be **structured, queryable, and durable** — not only embedded in prompts.

### Option A: PostgreSQL + pgvector (selected)

| Pros | Cons |
|------|------|
| JSONB for world model document; relational for audit | Requires Postgres ops (acceptable for enterprise target) |
| pgvector for semantic memory retrieval in Orient | Single-node scaling limits vs dedicated vector DB |
| ACID for approval tokens and risk budget | |
| One system for facts, events, vectors | |

### Option B: Redis + separate vector DB (Qdrant/Weaviate)

| Pros | Cons |
|------|------|
| Fast ephemeral loop state | Split-brain: world model consistency harder |
| Qdrant excellent at vector search | More moving parts for Phase 1 |
| Good for high-frequency Observe streams | Durability configuration complexity |

### Option C: Graph DB (Neo4j)

| Pros | Cons |
|------|------|
| Natural for contradiction / belief graphs | Overkill for initial world model schema |
| Rich relationship queries | Operational cost; team skill gap |
| | LLM update patterns map better to document + facts table |

**Selection rationale:** Postgres + pgvector matches "structured world model + semantic memory + audit in one store." Redis can be added later as an Observe stream cache without replacing orientation source of truth.

---

## 4. Audit and governance

### Option A: Append-only Postgres `audit_events` (selected)

| Pros | Cons |
|------|------|
| Intent/outcome split queryable by session | Not a full event-sourcing platform |
| Same DB as orientation | High volume may need partitioning later |
| Simple compliance export | |

### Option B: Kafka / event bus

| Pros | Cons |
|------|------|
| Scale, replay, multiple consumers | Heavy for Phase 0–1 |
| | Harder local dev story |

### Option C: JSONL files per session

| Pros | Cons |
|------|------|
| Trivial local dev | Weak concurrent access; no query |
| Git-friendly snapshots | Not production governance |

**Selection rationale:** Append-only SQL is sufficient until event volume forces Kafka. JSONL acceptable for local dev fixtures only.

---

## 5. LLM strategy

### Option A: Tiered models (selected approach)

| Phase | Model tier | Rationale |
|-------|------------|-----------|
| Observe (summarize signals) | Small / fast | High frequency, structured output |
| Orient (world model update) | Large / reasoning | Schwerpunkt — worth the tokens |
| Decide (candidates) | Large / reasoning | Multi-candidate planning |
| Act (tool selection) | Small or deterministic | Often schema-bound |
| IG&C pattern match | Small + rules | Hybrid: rules first, LLM fallback |

| Pros | Cons |
|------|------|
| Cost and latency optimized per phase | Routing logic to maintain |
| Orientation gets best model | Provider lock-in mitigated by adapter layer |

### Option B: Single model for all phases

| Pros | Cons |
|------|------|
| Simplicity | Expensive Observe; under-powered Orient on small models |
| | IG&C harder to separate |

**Selection rationale:** Boyd's theory explicitly says orientation dominates — allocate model quality there.

---

## 6. Human-in-the-loop delivery

### Option A: LangGraph interrupt + FastAPI SSE (selected)

| Pros | Cons |
|------|------|
| Graph pauses at checkpoint nodes | Requires SSE/long-poll client |
| Server pushes escalation payloads | |
| Maps to OpenSpec `human-in-the-loop` scenarios | |

### Option B: Email / ticket queue only

| Pros | Cons |
|------|------|
| Works for async enterprise | Too slow for tactical loops |
| | Poor UX for contradiction resolution |

**Selection rationale:** SSE checkpoint channel for Phase 1; ticket integration as Phase 2 adapter.

---

## 7. Observability

### Option A: OpenTelemetry + structured JSON logs (selected)

| Pros | Cons |
|------|------|
| Vendor-neutral traces across Observe sensors | Setup effort |
| Correlate loop_count, phase latency, confidence | |
| Export to Grafana/Datadog | |

### Option B: LangSmith-only

| Pros | Cons |
|------|------|
| Fast LLM trace setup | LLM-centric; misses non-LLM sensors |
| | Vendor lock-in for full system view |

**Selection rationale:** OTel for system traces; optional LangSmith for LLM prompt debugging during development.

---

## 8. Testing strategy

| Approach | Role |
|----------|------|
| **OpenSpec Gherkin scenarios** | Behavior contract (source of truth) |
| **pytest-bdd** | Executable specs from `openspec/specs/` |
| **Unit tests** | World model, contradiction detector, risk engine (no LLM) |
| **LLM eval fixtures** | Golden orientation updates with mocked LLM responses |

**Rejected:** End-to-end only testing — too flaky and slow for OODA loop iteration.

---

## Trade-off matrix (at a glance)

| Criterion | LangGraph + Python + Postgres | TS + Vercel AI + Redis | Temporal + Python |
|-----------|------------------------------|------------------------|-------------------|
| Time to Phase 1 prototype | ★★★★★ | ★★★★ | ★★ |
| OODA phase explicitness | ★★★★★ | ★★★ | ★★★★ |
| HITL / escalation | ★★★★★ | ★★★ | ★★★★★ |
| Operational weight | ★★★★ | ★★★★★ | ★★ |
| Orientation unity | ★★★★★ | ★★★★★ | ★★★★★ |
| Enterprise durability | ★★★★ | ★★★ | ★★★★★ |

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| LangGraph API churn | Pin versions; isolate graph definition in `runtime/graph.py` |
| World model context limits | Compression spec in `orientation-layer`; fact confidence thresholds |
| Contradiction over-triggering | Per-sensor tuning; severity calibration in deployment config |
| IG&C bypass abuse | Structural gates in spec; audit `igc_bypass` flag |
| Human bottleneck | Tiered approval: reversible vs irreversible paths |

---

## Phase 1 implementation boundary

**In scope:**

- `stub` and `manual` modes with CognitionPort (no external AI)
- SQLite local profile for test and operator demo
- Operator REST API + console + CLI for manual cognitive steps
- LangGraph-free OODA loop runner first (LangGraph optional in server profile)
- pytest-bdd in stub mode only for CI

**Out of scope (Phase 1D / later):**

- LiveCognition LLM API adapter (`live` mode)
- MCP bridge (`live` mode only)
- PostgreSQL server profile (demo uses SQLite)
- pgvector semantic memory (server profile)

---

## How to change this decision

1. Open an OpenSpec change (`/opsx:propose`) with updated requirements if behavior shifts.
2. Update this document with a new **Decision date** and **Status**.
3. Create Beads epic under `schwerpunkt` prefix for migration tasks.
4. Sync `openspec/project.md` tech stack table.
