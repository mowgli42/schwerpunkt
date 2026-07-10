# Operator Console

## Purpose

Define where human operators interact during **manual demo mode** and how those interactions map to OODA phases. The console and Operator API are the primary human touchpoints; they replace live AI for Orient and Decide without requiring MCP or LLM during demos or tests.

## Requirements

### Requirement: Operator API for human cognitive steps

The Operator API SHALL expose endpoints for each human-in-the-loop action required in manual mode.

#### Scenario: Operator resolves contradiction via API

- **GIVEN** a session in `manual` mode with an active contradiction on `case_status`
- **WHEN** operator POSTs `/sessions/{id}/resolve` with `fact_key=case_status`, `value=open`, `rationale=reopened by supervisor`
- **THEN** world model SHALL record `human_resolved_facts`
- **AND** the contradiction SHALL be cleared
- **AND** the OODA loop SHALL resume from Orient or Decide as appropriate

#### Scenario: Operator selects decision candidate

- **GIVEN** a session paused at Decide with candidates `[A, B, C]` published
- **WHEN** operator POSTs `/sessions/{id}/decide` with `candidate_id=B`
- **THEN** Decide SHALL complete with action B
- **AND** Act MAY proceed subject to risk and approval rules

#### Scenario: Operator issues approval for irreversible action

- **GIVEN** a pending irreversible action `close_case`
- **WHEN** operator POSTs `/sessions/{id}/approve` with `action_hash` matching `close_case`
- **THEN** the system SHALL issue a single-use `approval_token`
- **AND** Decide/Act MAY proceed with that token

### Requirement: Operator Console web UI

A browser console SHALL call the Operator API for all operator actions in manual demo mode.

#### Scenario: Console displays world model and contradictions

- **GIVEN** operator opens `/console` for an active manual session
- **WHEN** the page loads
- **THEN** the console SHALL display current loop phase, `loop_count`, world model facts, and active contradictions
- **AND** SHALL provide controls to resolve contradictions, pick candidates, and approve irreversible actions
- **AND** SHALL NOT require external AI services

#### Scenario: Console step advance in manual demo

- **GIVEN** operator completes Orient input for the current loop
- **WHEN** operator clicks **Advance** or equivalent
- **THEN** the runtime SHALL proceed to the next OODA phase
- **AND** audit events SHALL record operator actor id and timestamp

### Requirement: Observe panel without AI

Operators and fixtures SHALL inject observations without LLM involvement.

#### Scenario: Fixture sensor inject for demo

- **GIVEN** demo fixture `fixtures/scenarios/contradiction_case.json`
- **WHEN** operator or CLI loads the fixture into session Observe
- **THEN** Observe SHALL produce signals and confidence from the fixture
- **AND** no cognition backend SHALL be invoked during Observe

### Requirement: CLI parity for local demo

The CLI SHALL support the same manual flows as the console for headless local demos.

#### Scenario: CLI starts manual local session

- **GIVEN** operator runs `schwerpunkt session start --mode manual --profile local`
- **WHEN** the command succeeds
- **THEN** a session id SHALL be printed
- **AND** operator MAY POST resolutions via `schwerpunkt session resolve` subcommands
- **AND** no LLM or MCP configuration SHALL be required
