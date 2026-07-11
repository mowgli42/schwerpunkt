# Schwerpunkt — Living Spec Index

Capabilities map to Boyd OODA phases and cross-cutting concerns.

| Capability | OODA phase | Spec |
|------------|------------|------|
| **ooda-runtime** | Full loop | [ooda-runtime/spec.md](ooda-runtime/spec.md) |
| **orientation-layer** | Orient (schwerpunkt) | [orientation-layer/spec.md](orientation-layer/spec.md) |
| **human-in-the-loop** | Decide / Act gates | [human-in-the-loop/spec.md](human-in-the-loop/spec.md) |
| **runtime-modes** | stub / manual / live | [runtime-modes/spec.md](runtime-modes/spec.md) |
| **operator-console** | Human demo surfaces | [operator-console/spec.md](operator-console/spec.md) |
| **demo-scenarios** | Grok ticket fixtures | [demo-scenarios/spec.md](demo-scenarios/spec.md) |

## Planned (Phase 1+)

| Capability | OODA phase | Status |
|------------|------------|--------|
| observe-sensors | Observe | backlog |
| decide-risk-gate | Decide | backlog |
| act-audit | Act | backlog |
| implicit-guidance | IG&C fast path | backlog |
| live-cognition-adapter | Orient / Decide (live only) | backlog |
| mcp-bridge | Live tool calls | [mcp-bridge/spec.md](mcp-bridge/spec.md) |

## Implementation status model

Each requirement SHOULD carry front-matter or inline status:

| Status | Meaning |
|--------|---------|
| `specified` | Written in OpenSpec; no code |
| `implemented` | Code exists; not adversarially tested |
| `verified` | Gherkin or unit test proves behavior |
| `deferred` | Explicitly out of current phase |

Requirements SHALL NOT be closed in Beads until `verified` or explicitly deferred.

**Maturity:** L0 Specified → L1 Implemented → L2 Verified → L3 Production.  
Current repo: **L1** (contradiction demo path). See `docs/GROK-FEEDBACK.md`.

## Workflow

See [../WORKFLOW.md](../WORKFLOW.md). **Specs first** → Beads issues → implement → Gherkin → archive changes.

```bash
npx @fission-ai/openspec validate --specs --strict
```
