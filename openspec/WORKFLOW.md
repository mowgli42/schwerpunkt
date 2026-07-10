# Agent Workflow: OpenSpec + Gherkin + Beads

Follow this order unless the user explicitly requests a different approach.

## 1. Discovery & Specification (OpenSpec)

- Use `/opsx:explore` or `openspec` commands when adding or changing behavior.
- Create or update `openspec/specs/<capability>/spec.md` with:
  - Clear **Purpose**
  - Formal requirements using **SHALL** language
  - **GIVEN / WHEN / THEN / AND** scenarios (Gherkin-style)
- Validate: `npx @fission-ai/openspec validate [change-id] --strict`

## 2. Task Breakdown & Tracking (Beads)

- After creating or updating a spec, create Beads issues from requirements/scenarios.
- Map every requirement or scenario to one or more Beads issues (`--spec-id openspec/specs/...`).
- Before implementation: `bd ready` — work the highest-priority ready item.
- Update status: `bd update <id> --status in_progress`, `bd close <id>` when done.

### Bead status labels

| Status | Label | Meaning |
|--------|-------|---------|
| ⚪️ Backlog | `status:backlog` | Not yet broken down |
| 🔵 Specified | `status:specified` | OpenSpec spec with GWT scenarios |
| 🟠 Designed | `status:designed` | ADR / approach defined |
| 🟡 Implementing | `status:implementing` | Code in progress |
| 🟢 Verified | `status:verified` | Gherkin/pytest passing |
| ✅ Done | closed in Beads | Ready to archive OpenSpec change |

## 3. Implementation (Phase 1+)

- One Beads issue at a time (`bd ready`).
- OODA phases as explicit modules: `observe/`, `orient/`, `decide/`, `act/`.
- Orientation layer is persistent across loop iterations — never only in prompt context.

## 4. Validation

- Gherkin features mirror OpenSpec scenarios.
- `pytest` for unit tests on world model, contradiction detection, risk gating.
- Failing tests = spec or implementation bug — fix before closing Beads.

## 5. Archiving (OpenSpec)

- `openspec validate` before archive.
- `/opsx:archive` merges change deltas into living specs.

## Living specs

| Capability | Spec |
|------------|------|
| Index | `openspec/specs/README.md` |
| OODA runtime | `openspec/specs/ooda-runtime/spec.md` |
| Orientation layer | `openspec/specs/orientation-layer/spec.md` |
| Human-in-the-loop | `openspec/specs/human-in-the-loop/spec.md` |

## Communication rules

- Before implementation: run `bd ready` and state what you are working on.
- When proposing new work: spec first, then Beads, then code.
- Technology changes require updating `docs/TECHNOLOGY-SELECTION.md` and `openspec/project.md`.
