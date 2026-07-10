# Runtime Modes

## Purpose

The OODA runtime SHALL operate in modes that do not require external AI. Cognition (Orient and Decide) is injected via a `CognitionPort` so unit tests use stubs and operator demos use manual human input. Live LLM API and MCP adapters are optional and isolated behind `live` mode only.

## Requirements

### Requirement: Run mode configuration

The system SHALL support `stub`, `manual`, and `live` run modes selected at startup via `SCHWERKPUNKT_MODE` or CLI `--mode`.

#### Scenario: Stub mode for unit tests

- **GIVEN** `SCHWERPUNKT_MODE=stub`
- **AND** `SCHWERPUNKT_PROFILE=local`
- **WHEN** the application starts
- **THEN** the system SHALL use `StubCognition` for Orient and Decide
- **AND** SHALL NOT require LLM API keys
- **AND** SHALL NOT connect to an MCP server
- **AND** SHALL NOT perform outbound network calls for cognition

#### Scenario: Manual mode for operator demo

- **GIVEN** `SCHWERPUNKT_MODE=manual`
- **AND** `SCHWERPUNKT_PROFILE=local`
- **WHEN** the application starts
- **THEN** the system SHALL use `ManualCognition` for Orient and Decide
- **AND** SHALL block Orient/Decide until an operator submits input via Operator API
- **AND** SHALL NOT require LLM API keys or MCP

#### Scenario: Live mode enables external AI

- **GIVEN** `SCHWERPUNKT_MODE=live`
- **WHEN** the application starts with valid LLM or MCP configuration
- **THEN** the system SHALL use `LiveCognition` for Orient and Decide
- **AND** MAY call LLM API and/or MCP tools

### Requirement: CognitionPort abstraction

The OODA runtime SHALL depend only on `CognitionPort` and SHALL NOT import LLM or MCP client libraries in core loop modules.

#### Scenario: Runtime uses injected cognition

- **GIVEN** a test injects `StubCognition` with fixture `fixtures/cognition/orient_case_a.json`
- **WHEN** the OODA runtime completes an Orient phase
- **THEN** the result SHALL match the fixture
- **AND** no external AI client SHALL have been invoked

### Requirement: Local profile without Postgres

The `local` profile SHALL support test and demo without PostgreSQL.

#### Scenario: Local profile uses SQLite

- **GIVEN** `SCHWERPUNKT_PROFILE=local`
- **WHEN** the application starts
- **THEN** the system SHALL use SQLite for world model and audit persistence
- **AND** SHALL create the database file under `./data/` if missing

### Requirement: IG&C without LLM in stub and manual modes

IG&C fast path in `stub` and `manual` modes SHALL use rule tables, not LLM pattern matching.

#### Scenario: Rule-based IG&C in manual mode

- **GIVEN** `SCHWERPUNKT_MODE=manual`
- **AND** observation matches rule `retrieve_status` with risk class `reversible`
- **AND** confidence thresholds are met
- **WHEN** the runtime evaluates IG&C eligibility
- **THEN** IG&C MAY proceed without operator Decide input
- **AND** audit SHALL record `igc_bypass=true` and `igc_rule_id=retrieve_status`
