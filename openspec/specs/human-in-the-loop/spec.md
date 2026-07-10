# Human-in-the-Loop

## Purpose

AI can accelerate every OODA phase, but Boyd's orientation includes judgment that pattern-matching alone cannot replace. This capability defines structured sensemaking checkpoints, approval tokens for irreversible actions, and escalation paths.

## Requirements

### Requirement: Escalation triggers

The runtime SHALL escalate to human review when confidence, contradictions, risk budget, or approval requirements fail.

#### Scenario: Escalate on contradiction review

- **GIVEN** `requires_human_review` is true due to orientation contradictions
- **WHEN** Orient completes
- **THEN** the runtime SHALL pause before Decide
- **AND** escalation payload SHALL include world model snapshot, contradictions, and audit correlation id

### Requirement: Approval tokens for irreversible actions

Irreversible actions SHALL require a valid, single-use approval token bound to the action hash.

#### Scenario: Irreversible action blocked without token

- **GIVEN** a candidate action `close_case` with risk class `irreversible`
- **AND** no `approval_token` is present
- **WHEN** Decide evaluates candidates
- **THEN** `close_case` SHALL NOT be in `viable_candidates`
- **AND** Decide SHALL escalate OR select a reversible alternative if one exists

#### Scenario: Irreversible action with valid token

- **GIVEN** a candidate action `close_case` with risk class `irreversible`
- **AND** a valid `approval_token` bound to the action hash
- **WHEN** Decide evaluates candidates
- **THEN** `close_case` MAY be selected
- **WHEN** Act executes `close_case`
- **THEN** the `approval_token` SHALL be consumed
- **AND** audit log SHALL record approver identity and timestamp

### Requirement: Human contradiction resolution

Human resolution SHALL merge into world model as `human_resolved_facts` and clear related contradictions.

#### Scenario: Human resolves contradiction

- **GIVEN** escalation reason `contradiction_review`
- **AND** contradiction between `case_status` closed vs open
- **WHEN** human selects override `open` with rationale `reopened by supervisor`
- **THEN** world model SHALL record `human_resolved_facts` for `case_status` = `open`
- **AND** contradictions for `case_status` SHALL be cleared
- **AND** `orientation_confidence` SHALL be recalculated
- **AND** the agent MAY resume the OODA loop

### Requirement: Risk budget reset governance

Only humans with `risk_admin` role SHALL reset `risk_budget_remaining`.

#### Scenario: Risk budget reset is audited

- **GIVEN** a user with `risk_admin` role
- **WHEN** they reset `risk_budget_remaining` from 0 to 100 with rationale `post-incident review`
- **THEN** audit log SHALL record actor, prior value, new value, and rationale

### Requirement: Loop velocity guard

High-stakes sessions SHALL force sensemaking checkpoints to prevent outrunning human oversight.

#### Scenario: Forced checkpoint on loop velocity

- **GIVEN** session mode `high_stakes`
- **AND** `velocity_checkpoint_interval` is 10 loops
- **AND** `loop_count` mod 10 is 0
- **AND** all confidence thresholds are met
- **WHEN** the runtime completes Orient
- **THEN** the runtime SHALL pause for sensemaking checkpoint before Decide
