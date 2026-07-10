Feature: Human-in-the-loop governance
  Mirrors OpenSpec: human-in-the-loop
  Status: Grok adversarial scenarios (docs/GROK-FEEDBACK.md)

  Scenario: Legitimate numeric update is belief revision not contradiction
    Given a world model with account_balance 1000
    When observation reports account_balance 1005
    Then no contradiction is raised
    And account_balance is revised to 1005

  Scenario: Irreversible action consumes approval token
    Given a session with approval token for close_case
    When Act executes close_case with the token
    Then the token is consumed
    And audit records token_consumed true

  Scenario: Reused approval token is rejected
    Given a consumed approval token for close_case
    When Act attempts close_case again with the same token
    Then execution is blocked
    And escalation reason is invalid_or_consumed_approval_token

  Scenario: High stakes velocity checkpoint before Decide
    Given a high stakes session at loop count 10
    When Orient completes with sufficient confidence
    Then a velocity checkpoint pause is pending
