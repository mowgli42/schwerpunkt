# Schwerpunkt

**Orientation-first OODA loop architecture for production AI agents.**

> *Schwerpunkt* (German: focal point) is John Boyd's term for **Orientation** — the center of gravity of the OODA loop. Agents that cycle fast with a miscalibrated orientation cycle fast toward the wrong answer. This repo captures the conceptual design, technology trade-offs, and spec-driven roadmap for building agents that treat orientation as a first-class, persistent world model — not a transient chain-of-thought.

**Source concept:** [Boyd OODA Loop Agility AI Insights (Grok)](https://grok.com/share/c2hhcmQtMg_431da025-0818-430c-90ee-b21f66bd5a56)

## Status

Conceptual / pre-implementation. No runtime code yet — specifications, architecture, and technology selection drive what gets built.

## What this is

| Layer | Purpose |
|-------|---------|
| **Concept** | Boyd OODA applied to agentic AI: Observe → Orient → Decide → Act with implicit guidance, contradiction detection, and human-in-the-loop gates |
| **OpenSpec** | Living Gherkin-style requirements in `openspec/specs/` |
| **Beads** | Epic/task breakdown in `.beads/` (`bd ready` for next work item) |
| **Docs** | Architecture, technology trade-offs, and selection rationale |

## Core insight (vs ReAct)

Most agent frameworks use a **ReAct** loop: reason → act → observe tool result → repeat. Boyd's OODA loop differs in three ways that matter for high-stakes agents:

1. **Orientation is persistent** — a structured world model, not ephemeral CoT
2. **Implicit Guidance & Control (IG&C)** — trained patterns can skip explicit Decide when confidence and risk allow
3. **Observation quality gates decisions** — low-confidence sensing triggers escalation, not blind action

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/CONCEPT.md](docs/CONCEPT.md) | Full concept synthesis from Boyd + modern agent architecture research |
| [docs/OPERATOR-AND-RUN-MODES.md](docs/OPERATOR-AND-RUN-MODES.md) | **Where operators interact, local demands, stub/manual/live modes** |
| [docs/architecture.md](docs/architecture.md) | System architecture, data flows, domain objects |
| [docs/TECHNOLOGY-SELECTION.md](docs/TECHNOLOGY-SELECTION.md) | **Technology options, trade-offs, and recommended stack** |
| [openspec/WORKFLOW.md](openspec/WORKFLOW.md) | Spec → Beads → implement → verify workflow |
| [openspec/project.md](openspec/project.md) | Project context for agents |

## Run modes (no AI required for test & demo)

| Mode | Who does Orient/Decide | External AI |
|------|------------------------|-------------|
| `stub` | Fixture JSON | None — unit tests & CI |
| `manual` | **Operator** via console/API/CLI | None — live demos |
| `live` | LLM API and/or MCP | Optional production path |

```bash
SCHWERKPUNKT_MODE=manual SCHWERKPUNKT_PROFILE=local uvicorn schwerpunkt.api:app
# Operator: http://localhost:8000/console — no API keys needed
```

See **`docs/OPERATOR-AND-RUN-MODES.md`** for interaction surfaces and local system demands.

## Workflow

```bash
# Issue tracking
bd ready                    # next task
bd list                     # full hierarchy
bd show schwerpunkt-<id>    # task detail

# Specification
npx @fission-ai/openspec validate --specs --strict
```

## Living specs

| Capability | Spec |
|------------|------|
| Index | [openspec/specs/README.md](openspec/specs/README.md) |
| OODA runtime | [openspec/specs/ooda-runtime/spec.md](openspec/specs/ooda-runtime/spec.md) |
| Orientation layer | [openspec/specs/orientation-layer/spec.md](openspec/specs/orientation-layer/spec.md) |
| Human-in-the-loop | [openspec/specs/human-in-the-loop/spec.md](openspec/specs/human-in-the-loop/spec.md) |
| Runtime modes | [openspec/specs/runtime-modes/spec.md](openspec/specs/runtime-modes/spec.md) |
| Operator console | [openspec/specs/operator-console/spec.md](openspec/specs/operator-console/spec.md) |

## License

MIT (conceptual documentation and specs; implementation TBD)
