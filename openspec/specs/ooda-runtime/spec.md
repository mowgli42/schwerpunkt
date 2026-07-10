# OODA Runtime

## Purpose

Define the agent runtime that executes Boyd's OODA loop as an explicit, governable state machine — not an implicit ReAct chain. The runtime SHALL support parallel observation, persistent orientation, risk-gated decision, and verified action with feedback into the next cycle.

## Requirements

### Requirement: Loop structure

The runtime SHALL expose four phases (Observe, Orient, Decide, Act), maintain loop metadata, and persist checkpoint state between phases.

#### Scenario: Full OODA cycle for high-stakes action

- **GIVEN** an agent with risk class `irreversible` pending action
- **AND** observation confidence is 0.85
- **AND** orientation confidence is 0.72
- **AND** no active contradictions
- **WHEN** the runtime executes one loop iteration
- **THEN** Observe SHALL aggregate parallel sensor signals
- **AND** Orient SHALL update the world model
- **AND** Decide SHALL generate at least 2 candidate actions
- **AND** Decide SHALL filter candidates by risk budget
- **AND** Act SHALL log intent before execution
- **AND** Act SHALL verify postconditions after execution
- **AND** Act SHALL feed discrepancies back as observations for the next cycle

### Requirement: Implicit Guidance and Control (IG&C)

WHEN confidence and risk thresholds are met, the runtime MAY bypass explicit Decide (Observe → Act). IG&C SHALL always be audit-logged.

#### Scenario: IG&C fast path for low-risk reversible action

- **GIVEN** observation confidence is 0.9
- **AND** orientation confidence is 0.88
- **AND** matched IG&C pattern `retrieve_status` with risk class `reversible`
- **AND** no active contradictions
- **WHEN** the runtime executes one loop iteration
- **THEN** the runtime MAY skip explicit Decide
- **AND** Act SHALL still log intent and outcome
- **AND** the audit trail SHALL record `igc_bypass=true`

#### Scenario: IG&C blocked for irreversible action

- **GIVEN** a matched IG&C pattern exists
- **AND** action risk class is `irreversible`
- **WHEN** the runtime evaluates IG&C eligibility
- **THEN** the runtime SHALL NOT use IG&C
- **AND** the full Orient → Decide → Act path SHALL execute

### Requirement: Observation confidence gating

Low observation confidence SHALL block Decide and Act and trigger escalation.

#### Scenario: Escalate on low observation confidence

- **GIVEN** two critical sensors failed
- **AND** aggregate observation confidence is 0.4
- **WHEN** Observe completes
- **THEN** the runtime SHALL NOT invoke Decide
- **AND** the runtime SHALL escalate with reason `insufficient_observation_confidence`
- **AND** the escalation payload SHALL list failed sensors

### Requirement: Risk budget exhaustion

When risk budget is zero, Decide SHALL escalate and Act SHALL NOT execute.

#### Scenario: No action when risk budget exhausted

- **GIVEN** world model `risk_budget_remaining` is 0
- **AND** a viable candidate action exists
- **WHEN** Decide evaluates candidates
- **THEN** Decide SHALL return escalate with reason `risk_budget_exhausted`
- **AND** Act SHALL NOT execute

### Requirement: Loop termination

The runtime SHALL terminate with audit summary when objective complete, budget exhausted, max loops reached, or human abort.

#### Scenario: Terminate with audit summary

- **GIVEN** task objective is marked complete in world model
- **WHEN** the runtime evaluates termination
- **THEN** the runtime SHALL stop the loop
- **AND** emit a final world model snapshot
- **AND** emit an audit summary for the session
