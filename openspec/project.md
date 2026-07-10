# Schwerpunkt — Project Context

## Purpose

Schwerpunkt is a **conceptual reference implementation** of Boyd's OODA loop as a production AI agent architecture. The project prioritizes:

- **Orientation as schwerpunkt** — persistent world model, contradiction surfacing, confidence scoring
- **Governed autonomy** — risk budgets, irreversible-action gates, audit trails (intent vs outcome)
- **Agility without bookkeeping** — IG&C fast path for low-risk patterns; full loop for high-stakes decisions
- **Human sensemaking checkpoints** — structured pauses where AI accelerates but does not replace orientation

## Phase

**Phase 0 (concept):** OpenSpec living specs, technology selection ADR, Beads roadmap. No runtime until stack is locked and Phase 1 epic is specified.

## Tech stack (selected — see docs/TECHNOLOGY-SELECTION.md)

| Concern | Selection | Rationale |
|---------|-----------|-----------|
| Runtime language | **Python 3.12+** | LangGraph maturity, asyncio sensors, enterprise ML ops |
| Orchestration | **LangGraph** | Explicit OODA phase nodes, checkpointing, human-in-the-loop interrupts |
| Orientation store | **PostgreSQL + pgvector** | Structured world model + semantic retrieval in one system |
| Audit / events | **Append-only event log** (Postgres or JSONL) | Intent/outcome split for governance |
| API surface | **FastAPI** | SSE for observe streams, WebSocket optional |
| Verification | **pytest + Gherkin** | Spec-driven scenarios from OpenSpec |
| Specs | **OpenSpec** | `openspec/specs/` |
| Tasks | **Beads** | `.beads/` |

## Conventions

- Spec → Beads → implement → Gherkin (see `openspec/WORKFLOW.md`)
- Every irreversible action SHALL require an approval token in spec before code
- World model updates SHALL surface contradictions rather than silent overwrite
- IG&C fast path SHALL be gated by confidence + risk thresholds (not always-on)

## References

- [Grok concept share](https://grok.com/share/c2hhcmQtMg_431da025-0818-430c-90ee-b21f66bd5a56)
- Boyd OODA: orientation as focal point; implicit guidance and control
- [OODA Loop Architecture for Production AI Agents](https://superml.dev/ooda-loop-architecture-production-ai-agents-2026)
