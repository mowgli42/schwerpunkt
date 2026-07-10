# Schwerpunkt — Living Spec Index

Capabilities map to Boyd OODA phases and cross-cutting concerns.

| Capability | OODA phase | Spec |
|------------|------------|------|
| **ooda-runtime** | Full loop | [ooda-runtime/spec.md](ooda-runtime/spec.md) |
| **orientation-layer** | Orient (schwerpunkt) | [orientation-layer/spec.md](orientation-layer/spec.md) |
| **human-in-the-loop** | Decide / Act gates | [human-in-the-loop/spec.md](human-in-the-loop/spec.md) |

## Planned (Phase 1+)

| Capability | OODA phase | Status |
|------------|------------|--------|
| observe-sensors | Observe | backlog |
| decide-risk-gate | Decide | backlog |
| act-audit | Act | backlog |
| implicit-guidance | IG&C fast path | backlog |

## Workflow

See [../WORKFLOW.md](../WORKFLOW.md). **Specs first** → Beads issues → implement → Gherkin → archive changes.

```bash
npx @fission-ai/openspec validate --specs --strict
```
