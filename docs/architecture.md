# Schwerpunkt — System Architecture

Conceptual architecture for the OODA agent platform. Implementation follows OpenSpec living specs and the technology choices in [TECHNOLOGY-SELECTION.md](TECHNOLOGY-SELECTION.md).

## Where users interact

See [OPERATOR-AND-RUN-MODES.md](OPERATOR-AND-RUN-MODES.md) for full detail.

| Surface | Mode(s) | External AI |
|---------|---------|-------------|
| **Operator Console** (`/console`) | `manual` demo | No |
| **Operator API** (REST) | `manual`, `stub` tests | No |
| **CLI** (`schwerpunkt session …`) | `manual`, `stub` | No |
| **Fixture sensors** | `stub`, `manual` | No |
| **LLM API adapter** | `live` only | Yes |
| **MCP bridge** | `live` only | Yes |

## Run modes & local profile

```
SCHWERKPUNKT_MODE=stub|manual|live
SCHWERKPUNKT_PROFILE=local|server
         │
         ├─ stub  + local  → StubCognition + in-memory/SQLite  (unit tests, CI)
         ├─ manual + local → ManualCognition + SQLite         (operator demo)
         └─ live  + server → LiveCognition + Postgres          (production)
```

**Local demands (test + demo):** Python 3.12+, SQLite file, single process, no API keys, no network.

## High-level diagram

```mermaid
flowchart TB
  subgraph Clients["Clients"]
    Console["Operator Console\n(manual demo)"]
    CLI["CLI\n(manual / stub)"]
    API["Operator API\nREST + SSE"]
    MCP["MCP bridge\n(live only)"]
  end

  subgraph Runtime["OODA Runtime"]
    OBS["Observe\nparallel sensors"]
    ORI["Orient"]
    DEC["Decide"]
    ACT["Act\nexecute + verify"]
    OBS --> ORI --> DEC --> ACT
    ACT -.->|feedback| OBS
    ORI -.->|IG&C bypass| ACT
  end

  subgraph Cognition["CognitionPort (injected)"]
    STUB["StubCognition\ntests"]
    MAN["ManualCognition\ndemo"]
    LIVE["LiveCognition\nAPI / MCP"]
  end

  subgraph Schwerpunkt["Orientation Layer (persistent)"]
    WM["WorldModel\nfacts · contradictions · risk"]
  end

  subgraph Data["Store (profile-dependent)"]
    SQL[(SQLite local)]
    PG[(PostgreSQL server)]
  end

  Console --> API
  CLI --> API
  MCP -.->|live only| LIVE
  API --> Runtime
  ORI --> STUB & MAN & LIVE
  DEC --> STUB & MAN & LIVE
  ORI <--> WM
  WM --> SQL & PG
  ACT --> SQL & PG
```

## OODA phase responsibilities

| Phase | Module (planned) | Inputs | Outputs |
|-------|------------------|--------|---------|
| **Observe** | `observe/sensors.py` | Agent context, sensor registry | `Observation` (signals, failed_sensors, confidence) |
| **Orient** | `orient/world_model.py` | Observation, prior WorldModel | `OrientationResult` (updated model, contradictions, confidence) |
| **Decide** | `decide/planner.py` | OrientationResult | `Decision` (action, alternatives, escalate?) |
| **Act** | `act/executor.py` | Decision | `ActionResult` (outcome, verification, discrepancies) |

## Domain objects

### Observation

```python
# Conceptual — not implemented yet
Observation(
    signals: list[Signal],           # valid readings
    failed_sensors: list[str],
    timestamp: datetime,
    confidence: float,               # gates Orient/Decide
)
```

### WorldModel (schwerpunkt)

```python
WorldModel(
    task_objective: str,
    completed_steps: list[Step],
    pending_hypotheses: list[Hypothesis],
    known_facts: dict[str, FactWithConfidence],
    contradictions: list[Contradiction],
    irreversible_actions_taken: list[Action],
    active_constraints: list[Constraint],
    risk_budget_remaining: float,
    loop_count: int,
    elapsed_ms: int,
    deadline: datetime | None,
)
```

### Decision

```python
Decision(
    action: CandidateAction | None,
    escalate: Escalation | None,     # mutually exclusive with action
    alternatives_considered: list[CandidateAction],
    confidence: float,
    igc_bypass: bool,
)
```

### Audit event types

| Type | When | Purpose |
|------|------|---------|
| `intent` | Before Act | What agent planned |
| `outcome` | After Act | What actually happened |
| `escalation` | Decide/Orient gate | Why human needed |
| `human_resolution` | After checkpoint | Human orientation input |
| `igc_bypass` | Observe→Act skip | Fast path audit |
| `risk_budget_reset` | Admin action | Governance |

## IG&C (fast path) decision flow

```mermaid
flowchart TD
  O[Observe complete] --> C{confidence OK?}
  C -->|no| E[Escalate]
  C -->|yes| P{IG&C pattern match?}
  P -->|no| OR[Orient → Decide → Act]
  P -->|yes| R{risk reversible?}
  R -->|no| OR
  R -->|yes| X{contradictions?}
  X -->|yes| OR
  X -->|no| A[Act with igc_bypass=true]
```

## Data flow — one loop iteration

```mermaid
sequenceDiagram
  autonumber
  participant S as Sensors
  participant O as Observe
  participant R as Orient
  participant D as Decide
  participant H as Human
  participant A as Act
  participant DB as Postgres

  par Parallel observe
    S->>O: sensor reads
  end
  O->>R: Observation + confidence
  R->>DB: load world model
  R->>R: detect contradictions
  alt contradictions high severity
    R->>H: escalation (SSE)
    H->>R: human_resolved_facts
  end
  R->>D: OrientationResult
  alt IG&C eligible
    D->>A: direct action
  else full decide
    D->>D: candidates + risk gate
    alt irreversible w/o token
      D->>H: approval request
      H->>D: approval_token
    end
    D->>A: Decision
  end
  A->>DB: audit intent
  A->>A: execute + verify
  A->>DB: audit outcome
  A->>O: discrepancies as new signals
```

## Cross-cutting concerns

| Concern | Approach |
|---------|----------|
| Checkpointing | LangGraph checkpointer → Postgres |
| Correlation | `session_id` on all audit events |
| Confidence | Computed per phase; propagated multiplicatively |
| Compression | Orient summarizes low-confidence facts when over token budget |
| Testing | Unit tests without LLM; BDD from OpenSpec |

## Package layout (Phase 1 target)

```
schwerpunkt/
  openspec/              # Living specs
  docs/                  # Concept, architecture, tech selection
  src/
    schwerpunkt/
      runtime/           # LangGraph graph definition
      observe/
      orient/
      decide/
      act/
      api/               # FastAPI routes + SSE
      store/             # Postgres repositories
  tests/
    unit/
    features/            # Gherkin / pytest-bdd
  .beads/                # Issue tracking
```

## Related documents

- [CONCEPT.md](CONCEPT.md) — Boyd OODA synthesis
- [TECHNOLOGY-SELECTION.md](TECHNOLOGY-SELECTION.md) — stack trade-offs
- [../openspec/specs/README.md](../openspec/specs/README.md) — behavior contracts
