# Grok Feedback — Schwerpunkt Adversarial Review Response

**Source:** [Boyd OODA Loop Agility AI Insights (share)](https://grok.com/share/c2hhcmQtMg_70db4f3d-38b4-4377-b3f8-62af1efd8be9)  
**In response to:** `docs/GROK-RESEARCH-BRIEF.md` and PR #1  
**Date:** 2026-07-10

---

## Executive summary

Grok validated the adversarial brief: Schwerpunkt is **credible Phase-1 demo scaffolding**, not a Boyd OODA reference implementation. The biggest theory drift is treating the loop as a controllable phase machine rather than an orientation-centered, feedback-rich process.

**PR #1 score:** 8.5/10 — merge with minor polish.  
**Adversarial verdict:** Gaps in feedback, belief semantics, and governance are real but fixable without bloat.

---

## PR #1 review highlights

### Strengths
- Pragmatic `stub`/`manual`/`live` run modes (no LLM for CI/demo)
- Gherkin + OpenSpec alignment foundation
- Operator console + `demo-manual.sh`
- Beads discipline closing Phase 1A–1C

### Recommendations
1. Keep `GROK-RESEARCH-BRIEF.md` in `docs/` (research artifact, not PR noise)
2. Add fixture-driven contradiction/escalation cases in stub mode
3. Document IG&C bypass conditional edge; auth basics even for Phase 1
4. Console: world model + contradiction view
5. Phase 1D correctly backlogged

---

## Top 5 credibility gaps (prioritized)

| # | Gap | Boyd / agent theory | Priority |
|---|-----|---------------------|----------|
| 1 | No Act→Observe discrepancy feedback | Action tests hypothesis; discrepancies must update orientation | **P0** |
| 2 | Naive binary contradiction (no belief revision) | Orientation needs analyses/synthesis; AGM-style minimal change | **P0** |
| 3 | Approval token not consumed/bound at Act | Governance theater; intent→execution linkage required | **P0** |
| 4 | IG&C bypasses operator Decide in manual mode | Manual mode should be orientation checkpoint unless explicit fast-path | **P1** |
| 5 | No velocity guard / high-stakes checkpoint | Tempo without orientation quality → error | **P1** |

---

## Validated vs contextualized gaps

### Validated (real theory drift)
- Act→Observe feedback missing (`verification_matches` always true)
- Belief revision absent (1000→1005 triggers contradiction)
- Approval token issued but never consumed
- Strict phase enum vs Boyd's overlapping continuous model
- Decide ranking / operator choice bugs in manual flow

### Contextualized (demo-acceptable for now)
- Parallel Observe sensors — aspirational; fixtures OK for Phase 1
- IG&C in manual mode — **feature if scoped** (advisory/preview by default)
- CognitionPort leakage — maintainability issue, not theory violation
- Audit not governance-grade — acceptable for demo with caveats

---

## IG&C in manual mode: feature, not violation

Boyd explicitly supports IG&C as mature low-friction behavior when orientation is sound.

**Repo policy (adopted):**
- In `manual` mode, IG&C is **disabled by default** (operator must Decide)
- In `stub` mode, IG&C remains enabled for fast-path demos
- Opt-in: `SCHWERKPUNKT_IGC_MANUAL=1` for manual IG&C testing
- Future `high_stakes` sessions: IG&C disabled until explicit operator confirmation

---

## Phase 2 scope (falsifiable, not enterprise bloat)

**Goal:** L2 Verified — spec-traceable reference with adversarial Gherkin.

| In scope | Out of scope |
|----------|--------------|
| One full loop with orchestration interrupts (LangGraph or equivalent) | Multi-tenant, WORM audit |
| `human-in-the-loop.feature` passing (token, discrepancy, belief revision) | Edge sensors, multi-agent swarms |
| Measurable Boyd metrics in demo | Production auth/RBAC |
| Mock multi-signal Observe + parallel failure | pgvector scale |
| AGM-inspired belief revision in orientation-layer | |
| One adversarial demo: irreversible + token + discrepancy | |

**Falsification test:** Does the loop demonstrably update orientation from action outcomes with minimal belief change?

---

## OpenSpec / Gherkin additions (from Grok)

See `features/human-in-the-loop.feature` for:
- Approval token consumption and hash binding
- Act→Observe discrepancy feedback
- Belief revision vs contradiction (numeric tolerance)
- Velocity guard / high-stakes checkpoint

Add `implementation_status` per requirement: `specified | implemented | verified | deferred`.

---

## Maintainer actions (this iteration)

- [x] Capture Grok feedback in this document
- [x] Disable IG&C in manual mode by default
- [x] Wire `consume_approval_token` in Act
- [x] Belief revision for numeric fact updates
- [x] Act→Observe discrepancy population
- [x] Fix manual Decide to honor operator candidate choice
- [x] Add `features/human-in-the-loop.feature` + unit tests
- [ ] Reopen Beads tasks for SSE, velocity guard full spec, LangGraph
- [ ] Add maturity matrix (L0–L3) to README
- [ ] Operator console world-model view

---

## Suggested follow-on issues

1. Refine operator console with world model + contradiction view
2. Postgres profile for manual/live (Docker compose)
3. MTO Decision Tree as first real sensor use case
4. Live LLM/MCP adapters (Phase 1D) with provider abstraction
5. LangGraph orchestration or revise TECHNOLOGY-SELECTION to "deferred"
