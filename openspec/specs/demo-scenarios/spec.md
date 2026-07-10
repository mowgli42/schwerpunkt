# Demo scenarios (Grok OODA tickets → executable fixtures)

## Purpose

Executable demo and test scenarios derived from Boyd OODA Grok concept tickets. Each scenario maps to `fixtures/scenarios/*.json`, optional `fixtures/cognition/<scenario>/`, and Gherkin in `features/runtime-modes.feature`.

## Requirements

### Requirement: Contradiction case demo

The contradiction_case scenario SHALL seed a closed case and observe an open signal for operator resolution.

#### Scenario: Operator demo contradiction flow

- **GIVEN** fixture `fixtures/scenarios/contradiction_case.json`
- **AND** `SCHWERKPUNKT_MODE=manual`
- **WHEN** the operator loads the fixture and advances the loop
- **THEN** the runtime SHALL pause with `pending_operator.kind=orient`
- **WHEN** the operator resolves `case_status` to `open`
- **THEN** contradictions SHALL be cleared
- **AND** the loop SHALL proceed toward Decide without LLM or MCP

### Requirement: IG&C retrieve status demo

The igc_retrieve scenario SHALL trigger rule-based IG&C bypass in stub and manual modes.

#### Scenario: IG&C demo without Decide input

- **GIVEN** fixture `fixtures/scenarios/igc_retrieve.json` with `pattern_id=retrieve_status`
- **AND** observation confidence at least 0.8
- **WHEN** the runtime executes one loop iteration in stub mode
- **THEN** audit SHALL record `igc_bypass` or decision SHALL have `igc_bypass=true`
- **AND** no external AI SHALL be invoked

### Requirement: Risk budget exhaustion demo

The risk_budget_exhausted scenario SHALL escalate when `risk_budget_remaining` is zero.

#### Scenario: Risk budget blocks action

- **GIVEN** session `risk_budget_remaining` is 0
- **WHEN** Decide evaluates after Orient
- **THEN** escalation reason SHALL be `risk_budget_exhausted`

### Requirement: Headless demo script

The repository SHALL provide `scripts/demo-manual.sh` that completes contradiction_case without external AI.

#### Scenario: CLI demo runs offline

- **GIVEN** `scripts/demo-manual.sh` is executable
- **WHEN** the script runs with no API keys and no network
- **THEN** it SHALL exit 0 after completing contradiction_case operator steps
