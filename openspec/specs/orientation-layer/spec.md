# Orientation Layer

## Purpose

Orientation is the **schwerpunkt** of the OODA loop: the persistent mental model through which all observations are interpreted. This capability specifies the world model, contradiction handling, and confidence scoring that separate OODA agents from ReAct chains.

## Requirements

### Requirement: World model structure

The orientation layer SHALL maintain a structured, serializable WorldModel that persists across tool calls and loop iterations.

#### Scenario: World model persists across loop iterations

- **GIVEN** a completed Orient phase with `known_facts` containing `account_balance=1000`
- **WHEN** a new Observe phase completes in the same session
- **THEN** Orient SHALL load the prior WorldModel from persistent store
- **AND** SHALL NOT rely solely on LLM context window for prior facts

### Requirement: Contradiction detection

Orient SHALL detect contradictions before merging observations and SHALL NOT silently overwrite high-confidence prior beliefs.

#### Scenario: Clean orientation update without contradiction

- **GIVEN** a world model with `known_fact` `account_balance` = 1000 (confidence 0.95)
- **AND** a new observation signal `account_balance` = 1005 (confidence 0.9)
- **AND** no contradiction between signals
- **WHEN** Orient runs
- **THEN** `known_facts` SHALL update `account_balance` to 1005
- **AND** `contradictions` SHALL remain empty
- **AND** `orientation_confidence` SHALL be >= 0.8
- **AND** `requires_human_review` SHALL be false

#### Scenario: Contradiction blocks silent overwrite

- **GIVEN** `known_fact` `case_status` = `closed` (confidence 0.92)
- **AND** new observation signal `case_status` = `open` (confidence 0.85)
- **WHEN** Orient runs
- **THEN** `contradictions` SHALL contain one high-severity entry
- **AND** `known_facts` SHALL NOT replace `closed` with `open` without resolution
- **AND** `requires_human_review` SHALL be true
- **AND** `orientation_confidence` SHALL be < 0.5

### Requirement: Orientation confidence floor

When orientation confidence is below threshold, Decide SHALL refuse to select an action.

#### Scenario: Low orientation confidence blocks decision

- **GIVEN** `orientation_confidence` is 0.25
- **WHEN** Orient completes and Decide is invoked
- **THEN** Decide SHALL escalate with reason `insufficient_orientation_confidence`
- **AND** SHALL NOT return an executable action

### Requirement: World model compression

When token limits are exceeded, Orient SHALL compress while preserving critical state.

#### Scenario: Compression preserves contradictions and irreversible actions

- **GIVEN** a world model exceeding `token_limit`
- **AND** 50 low-confidence facts (confidence < 0.5)
- **AND** 3 active high-severity contradictions
- **AND** 2 `irreversible_actions_taken`
- **WHEN** Orient compresses the world model
- **THEN** `contradictions` SHALL remain fully enumerated
- **AND** `irreversible_actions_taken` SHALL remain fully enumerated
- **AND** facts with confidence > 0.7 SHALL be preserved verbatim
- **AND** compression SHALL be audit-logged
