Feature: Schwerpunkt OODA platform
  Mirrors OpenSpec: runtime-modes, ooda-runtime, operator-console

  Scenario: Stub mode for unit tests
    Given SCHWERKPUNKT_MODE is stub
    And SCHWERKPUNKT_PROFILE is local
    When the application starts
    Then StubCognition is used
    And no LLM API keys are required

  Scenario: Local profile uses SQLite path
    Given SCHWERKPUNKT_PROFILE is local
    When the store is created
    Then the database path is under data directory

  Scenario: IG&C fast path for low-risk reversible action
    Given a stub session with scenario igc_retrieve
    When the runtime executes one loop iteration
    Then IG&C bypass may be recorded in audit

  Scenario: No action when risk budget exhausted
    Given a stub session with risk budget 0
    When Decide evaluates candidates
    Then escalation reason is risk_budget_exhausted

  Scenario: Operator resolves contradiction via API
    Given a manual session with scenario contradiction_case
    When the operator loads the observe fixture
    And the operator advances the loop
    Then a contradiction orient pause is pending
    When the operator resolves case_status to open
    Then contradictions are cleared

  Scenario: Fixture sensor inject for demo
    Given demo fixture contradiction_case
    When the fixture is loaded into observe
    Then observation confidence is at least 0.8
    And no cognition backend is invoked during observe
