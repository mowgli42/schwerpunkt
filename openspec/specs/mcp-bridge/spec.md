# MCP Bridge

## Purpose

Optional Model Context Protocol tool bridge for live-mode Observe. Stub and manual modes SHALL NOT require MCP. Unit tests SHALL use `SCHWERKPUNKT_MCP_MOCK=1` without a running MCP server.

## Requirements

### Requirement: MCP observe opt-in

Live mode SHALL load observations via MCP tools only when `mcp_enabled` is true.

#### Scenario: Mock MCP observe in tests

- **GIVEN** `SCHWERPUNKT_MODE=live`
- **AND** `mcp_enabled=true`
- **AND** `SCHWERKPUNKT_MCP_MOCK=1`
- **WHEN** operator POSTs `/sessions/{id}/observe/mcp` with tool `fetch_sensor`
- **THEN** the session SHALL receive an `Observation` with MCP-sourced signals
- **AND** no external MCP server SHALL be contacted

#### Scenario: MCP disabled outside live mode

- **GIVEN** `SCHWERPUNKT_MODE=stub`
- **WHEN** operator POSTs `/sessions/{id}/observe/mcp`
- **THEN** the API SHALL reject the request with an error indicating MCP is unavailable
