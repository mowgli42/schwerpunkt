# Grok Research Brief — Adversarial Review of Schwerpunkt

**Purpose:** Feed this document to Grok for additional research, critique, and design feedback.  
**Grok response:** See [GROK-FEEDBACK.md](GROK-FEEDBACK.md) (from [share link](https://grok.com/share/c2hhcmQtMg_70db4f3d-38b4-4377-b3f8-62af1efd8be9)).  
**Repo:** https://github.com/mowgli42/schwerpunkt  
**Concept source:** [Boyd OODA Loop Agility AI Insights](https://grok.com/share/c2hhcmQtMg_431da025-0818-430c-90ee-b21f66bd5a56)  
**Review date:** 2026-07-10

---

## Executive verdict (adversarial)

**OpenSpec design is NOT complete.** The living specs describe a production-grade Boyd OODA agent platform. The implementation is a **Phase-1 vertical slice** that demonstrates one happy-path operator demo (`contradiction_case`) with fixture-driven stub/manual modes.

`openspec validate --specs --strict` passing means **markdown structure is valid**, not that behavior is implemented. Beads tasks marked closed overstate fidelity to acceptance criteria (e.g. "SSE escalation endpoint" has no SSE).

| Layer | Claimed | Actual |
|-------|---------|--------|
| OpenSpec scenarios | ~30+ across 6 specs | ~35% have any test; ~15% fully implemented |
| Gherkin verification | Spec-driven | 6 scenarios, 2 specs thinly covered, weak "MAY" assertions |
| Operator demo | Multi-scenario | Only `contradiction_case` scripted end-to-end |
| Boyd OODA fidelity | Continuous loop, orientation schwerpunkt | Sequential state machine; orientation logic split across SessionManager |
| Tech selection ADR | LangGraph + SSE + Postgres | Plain Python loop; no LangGraph; no SSE; SQLite only |

---

## 1. Spec vs implementation matrix (research Grok should validate)

### `ooda-runtime` — largely unimplemented

| Spec requirement | Implemented? | Evidence / gap |
|------------------|--------------|----------------|
| Parallel Observe sensors | **No** | Fixtures load JSON; no `asyncio.gather`, no sensor registry |
| ≥2 Decide candidates | **Partial** | Stub fixtures yes; manual mode hardcodes A/B/C in `session.py` |
| Act postcondition verification | **No** | `verification_matches` always `True`; no expected vs actual |
| Discrepancies → next Observe | **No** | `ActionResult.discrepancies` never populated; no feedback edge |
| IG&C audit `igc_bypass=true` | **Partial** | Logged as event type `igc_bypass`, not field on decision in audit |
| IG&C blocked for irreversible | **Untested** | No rule or test for irreversible IG&C pattern |
| Low observation confidence escalation | **Partial** | Hardcoded `confidence < 0.5 and len(failed_sensors) >= 2`; no "critical sensor" model |
| Loop termination + audit summary | **Partial** | `objective_complete` only via magic action name `mark_complete`; no max-loops, no human abort |
| Checkpoint persistence between phases | **Partial** | Session JSON in SQLite; phase transitions are manual/fragile |

**Grok research question:** What is the minimum architecture for true Act→Observe feedback without collapsing into ReAct? Cite production OODA agent patterns (e.g. SPINE, SuperML OODA article).

---

### `orientation-layer` — core only

| Spec requirement | Implemented? | Gap |
|------------------|--------------|-----|
| World model persistence | **Yes** | SQLite session blob |
| Contradiction detection | **Yes** | Naive value inequality; no numeric tolerance, temporal decay, or source trust |
| Block silent overwrite | **Yes** | High-severity path works |
| Orientation confidence floor | **Partial** | Threshold 0.3 in decide; not wired to all paths |
| World model compression | **No** | Spec exists; zero code |
| `pending_hypotheses`, `active_constraints`, `deadline` | **No** | Fields in model; unused |

**Grok research question:** How should orientation handle **legitimate updates** vs contradictions (e.g. account balance 1000→1005)? Current engine treats any value change as potential contradiction if key exists. Boyd-oriented systems likely need **belief revision** semantics, not binary equality.

---

### `human-in-the-loop` — mostly spec-only

| Spec requirement | Implemented? | Gap |
|------------------|--------------|-----|
| Escalation payload with correlation id | **No** | No correlation ids |
| Approval token single-use + bound to action hash | **No** | Token generated and stored; **`consume_approval_token` never called** in Act |
| Irreversible blocked without token | **Partial** | `decide_with_risk` filters; demo never exercises B→approve→act |
| Risk budget reset by `risk_admin` | **No** | No roles, no endpoint |
| Loop velocity guard (`high_stakes`) | **No** | No session mode, no forced checkpoint |
| SSE escalation stream | **No** | Beads task closed; API is poll-only POST |

**Grok research question:** What HITL patterns prevent "approval theater" (token issued but not cryptographically bound to executed action)? Research governance models for agentic systems under EU AI Act / NIST AI RMF framing.

---

### `operator-console` — thin vertical slice

| Spec requirement | Implemented? | Gap |
|------------------|--------------|-----|
| REST resolve/decide/approve | **Yes** | Works for happy path |
| Console displays world model | **Yes** | Static HTML + fetch |
| Console step advance | **Yes** | |
| CLI parity | **Yes** | Separate SessionManager per CLI invocation; relies on SQLite |
| Fixture inject without cognition on Observe | **Yes** | |

**Grok research question:** What UX patterns best support Boyd's "sensemaking checkpoint" vs simple approve/deny? Research operator consoles for SOC, air traffic, clinical decision support.

---

### `runtime-modes` — stub/manual yes, live no

| Mode | Status |
|------|--------|
| `stub` | Works |
| `manual` | Works with caveats (IG&C can skip operator Decide) |
| `live` | `NotImplementedError` — correct for Phase 1D |

**Design tension for Grok:** Manual demo goal is "operator performs Orient/Decide." IG&C in manual mode can auto-Act after Orient, **bypassing operator Decide** on `igc_retrieve`. Is that consistent with the concept or a spec bug?

---

## 2. Architectural adversarial findings

### 2.1 CognitionPort is bypassed in manual mode

`SessionManager._orient` and `_decide` branch on `isinstance(ManualCognition)` and embed domain logic inline (hardcoded candidates, thresholds). `ManualCognition` class is a stub. This violates the stated abstraction: *"OODA runtime SHALL depend only on CognitionPort."*

**Grok research:** Compare port/adapter vs embedded branching for human-in-the-loop agents. When does splitting cognition by mode create untestable duplication?

### 2.2 OODA is a phase enum, not Boyd's loop

Boyd emphasizes overlapping feedback and orientation as schwerpunkt. Implementation:

```
OBSERVE → ORIENT → DECIDE → ACT → (phase = OBSERVE)
```

No parallel paths; `PAUSED` is a dead state until operator POST; `resolve_contradiction` jumps phase to `DECIDE` skipping re-orient semantics in spec.

**Grok research:** Map Boyd's original briefing diagrams to implementable state machines. Is explicit phase enum incompatible with "continuous loop"?

### 2.3 Decide ranking is inverted

`decide_with_risk` selects `max(viable, key=lambda x: -x.expected_cost)` — highest cost wins, not highest expected value. Comment in concept docs says "highest-value viable candidate."

### 2.4 Audit trail is not governance-grade

- Only last 3 audit events persisted to `audit_events` table per `_persist`
- Intent/outcome split exists but no diff between planned vs actual
- No immutable append-only guarantee (session row is REPLACE)

**Grok research:** Audit requirements for autonomous agents in regulated domains (finance, healthcare, defense). WORM logs vs CRUD session store.

### 2.5 Security surface (even for demo)

- No auth on operator API
- Session IDs are 8-char UUID prefix (brute-forceable in shared deployments)
- Approval tokens: `secrets.token_hex(8)` with no binding verification at execution

---

## 3. Test / Gherkin adversarial audit

**14 tests pass** — confidence should be low:

| Issue | Example |
|-------|---------|
| Weak assertions | "IG&C bypass **may** be recorded" |
| No spec traceability | `human-in-the-loop`, `orientation-layer` compression, `ooda-runtime` full cycle — **zero** Gherkin |
| BDD async smell | `asyncio.get_event_loop().run_until_complete` in sync steps |
| API test incomplete | Stops after resolve; doesn't assert `loop_count`, irreversible path, or audit |
| No negative tests | `live` mode, invalid session, double token consume |
| Fixture-only Observe | Never tests multi-sensor parallel failure modes from spec |

**Grok research:** Property-based testing for world-model consistency; mutation testing on contradiction detector; Gherkin coverage metrics tied to OpenSpec requirement IDs.

---

## 4. Documentation / process drift

| Document | Drift |
|----------|-------|
| `TECHNOLOGY-SELECTION.md` | Says LangGraph selected; not in codebase |
| `architecture.md` | SSE in diagrams; not implemented |
| `openspec/project.md` | Lists LangGraph, Postgres, pgvector |
| Beads `1.5` | Closed with "SSE escalation" — not delivered |
| Beads `1.6` | Closed with "scenarios cover runtime-modes and operator-console" — partial at best |

**Grok research:** How should spec-driven projects mark requirements as *specified* vs *implemented* vs *verified*? Propose a status model (e.g. ISO 29148-style).

---

## 5. What IS honestly complete (credit where due)

1. **Contradiction demo path** — operator can resolve `case_status` and complete one loop in manual/stub modes.
2. **Cognition isolation for CI** — stub/manual require no LLM/MCP (design intent met for test/demo).
3. **IG&C rule table** — JSON rules, works for `retrieve_status` in stub.
4. **OpenSpec as contract skeleton** — good foundation if tagged with implementation status.
5. **Operator surfaces** — API + console + CLI trifecta exists (minimal but real).

---

## 6. Research tasks for Grok (prioritized)

### A. Boyd fidelity

1. Does orientation-as-schwerpunkt require a **single unified world-model service**, or is split between SessionManager + CognitionPort acceptable?
2. How should **IG&C** coexist with mandatory human orientation checkpoints in high-stakes mode?
3. What does "operate inside the opponent's OODA loop" imply for **multi-agent** systems — is CrewAI rejection still correct?

### B. Production patterns

4. Compare **LangGraph interrupts** vs custom pause/resume vs **Temporal** for HITL waits measured in minutes/hours.
5. Best practice for **intent vs outcome audit** with LLM non-determinism.
6. **Belief revision** algorithms when observations refine (not contradict) prior facts.

### C. Spec completeness

7. Propose a **capability maturity matrix** for this repo (L0 concept → L1 demo → L2 verified → L3 production).
8. Which missing scenarios are **blocking** for a credible Boyd OODA reference implementation vs nice-to-have?
9. Should `live` mode use **LLM API for Orient/Decide** and **MCP only for Observe tools**, or unified MCP?

### D. Operator UX

10. Research sensemaking checkpoint UX: what must the operator see beyond raw facts/contradictions?
11. How to demo **velocity guard** and **risk budget reset** without boring the audience?

### E. Adversarial test scenarios Grok should propose

| # | Scenario | Expected behavior | Currently |
|---|----------|-------------------|-----------|
| 1 | Operator chooses irreversible B without approve | Blocked | Theoretically yes; **untested** |
| 2 | Approve then execute | Token consumed | **Token not consumed** |
| 3 | IG&C during manual demo | Operator should Decide? | **Skipped** |
| 4 | Numeric fact drift (1000→1005) | Update not contradiction | **May false-positive** |
| 5 | 15 rapid loops in high_stakes | Forced checkpoint | **Not implemented** |
| 6 | Sensor 1 conflicts sensor 2 same observe | Contradiction in observe phase | **Not implemented** |
| 7 | Act outcome ≠ intent | Discrepancy feeds Observe | **Not implemented** |
| 8 | `live` mode startup | Clear error / disabled | **Raises at orient** |

---

## 7. Suggested OpenSpec status model (for Grok to refine)

Add to each requirement:

```yaml
status: specified | implemented | verified | deferred
verified_by: tests/features/foo.feature#scenario-name
```

Until status is `verified`, requirement SHALL NOT be marked closed in Beads.

---

## 8. Prompt to paste into Grok

```
You previously helped define "Boyd OODA Loop Agility AI Insights" for Schwerpunkt
(orientation-first agent architecture). An implementation now exists:
https://github.com/mowgli42/schwerpunkt

Read docs/GROK-RESEARCH-BRIEF.md (adversarial review) and:
1. Validate or refute each gap against Boyd's original OODA theory and modern agent literature.
2. Prioritize the top 5 spec gaps that undermine "schwerpunkt" credibility.
3. Propose concrete OpenSpec scenario additions with Gherkin (especially: approval token consume,
   Act→Observe feedback, belief revision vs contradiction, velocity guard).
4. Recommend whether IG&C in manual operator mode is a feature or a spec violation.
5. Suggest a credible Phase 2 scope that is still "conceptual" but falsifiable — not enterprise bloat.

Be adversarial. Cite sources. Distinguish demo-quality from production-quality.
```

---

## 9. Recommended repo actions (post-Grok)

*Not for Grok — for maintainers after feedback:*

1. Reopen or split Beads tasks for SSE, approval consume, Gherkin coverage per spec file.
2. Add `implementation_status` front-matter to each OpenSpec spec.
3. Downgrade README "complete demo" to "contradiction_case demo; see maturity matrix."
4. Either implement LangGraph or revise TECHNOLOGY-SELECTION to "deferred."
5. Add one adversarial Gherkin feature: `features/human-in-the-loop.feature`.
