# Schwerpunkt — Concept Synthesis

> Derived from [Boyd OODA Loop Agility AI Insights (Grok)](https://grok.com/share/c2hhcmQtMg_431da025-0818-430c-90ee-b21f66bd5a56) and cross-referenced with production agent architecture literature.

## The problem with ReAct as default

**ReAct** (Reason + Act interleaved) is the dominant mental model for AI agents: the model reasons, picks a tool, observes the result, reasons again. It is clean, well-documented, and sufficient for retrieval-heavy or low-stakes workflows.

It systematically **understates** what matters in enterprise and operational agents:

| ReAct assumption | OODA reality |
|------------------|--------------|
| Last tool output = observation | Observations are **multi-signal**, parallel, with varying reliability |
| Reasoning string = state | **Orientation** is a persistent world model — beliefs, contradictions, risk |
| First reasonable action wins | **Decide** generates candidates, risk-gates, considers reversibility |
| Success = terminal tool result | **Act** verifies postconditions; discrepancies feed the next cycle |
| Speed = more iterations | **Agility** = better orientation, not faster bookkeeping |

John Boyd designed the OODA loop for fighter pilots: radar contacts that might be friendly, hostile, or artifacts; decisions in milliseconds; **wrong decisions are immediately irreversible**. That is structurally closer to production agent risk than a chatbot with tools.

## Boyd's OODA (not the slide version)

The tourist diagram is four boxes in a circle: Observe → Orient → Decide → Act. Boyd's actual model adds:

### 1. Orientation is the schwerpunkt

Orientation synthesizes cultural traditions, prior experience, mental models, and incoming data. It is not one step — it is the **lens** for every other phase. A pilot (or agent) with wrong orientation observes the same contact and concludes worse.

**For AI agents:** system prompt, retrieved context, belief state, and structured memory are the orientation layer. Miscalibrated orientation → correct reasoning within a wrong frame → confidently wrong outcomes.

### 2. Implicit Guidance and Control (IG&C)

Experienced operators sometimes go **Observe → Act**, bypassing explicit Orient and Decide. This is not a bug — trained orientation already encodes the decision. Boyd called this *implicit guidance and control*.

**For AI agents:** pattern-matched fast paths are valuable **when gated** by confidence, reversibility, and absence of contradictions. Ungated IG&C is reckless automation.

### 3. Continuous, overlapping feedback

Orientation shapes what you observe. Action generates new observations. Multiple feedback paths run in parallel — not a strict sequential clock.

## The Schwerpunkt architecture (conceptual)

```
┌─────────────────────────────────────────────────────────┐
│                 OODA Agent Runtime                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │ OBSERVE  │──▶│  ORIENT  │──▶│  DECIDE  │            │
│  │ sensors  │   │ world    │   │ planner  │            │
│  │ parallel │   │ model    │   │ + risk   │            │
│  └────┬─────┘   └──────────┘   └────┬─────┘            │
│       │         ┌──────────┐        │                  │
│       └─────────│   ACT    │◀───────┘                  │
│                 │ execute  │                           │
│                 │ verify   │                           │
│                 │ audit    │                           │
│                 └──────────┘                           │
│  ┌─────────────────────────────────────────────────┐  │
│  │     Orientation Layer (persistent schwerpunkt)   │  │
│  │  facts · contradictions · risk budget · memory   │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Observe — multi-signal sensing

- Sensors run **in parallel** (APIs, DB, streams, human input).
- Failed sensors are first-class; observation carries **confidence**.
- Low confidence → slow down, escalate, or wait — not blind proceed.

### Orient — world model maintenance

- Structured state: facts with confidence, contradictions, hypotheses, constraints.
- **Contradictions surfaced**, not silently merged.
- Compression at scale with audit of what was dropped.

### Decide — candidates + risk gating

- Generate **multiple** candidates; select after risk assessment.
- Irreversible actions require **approval tokens**.
- **Risk budget** depletes with consequential actions; exhaustion → escalate.

### Act — execute, verify, audit

- **Intent log** before execution; **outcome log** after.
- Postcondition verification; discrepancies become next observations.
- Gap between intent and outcome = primary debug and governance signal.

## LLMs reshaping the loop (caution)

LLMs accelerate every phase: more data in Observe, pattern proposals in Orient, option expansion in Decide, logistics in Act. But LLM "orientation" is **pattern-matching over training corpus**, not lived judgment.

**Design implication:** deliberate **sensemaking checkpoints** where humans perform genuine orientation — reviewing conflicts, overriding beliefs, resetting risk budget — rather than rubber-stamping AI conclusions.

## Anti-patterns

| Anti-pattern | Why it fails |
|--------------|--------------|
| OODA as stage-clock KPIs | Optimizing loop *speed* without orientation quality |
| Orientation only in prompt | Lost every context window; no contradiction memory |
| IG&C always on | Irreversible actions without governance |
| Silent contradiction merge | Error compounds across fast cycles |
| Human review as afterthought | Loop outruns oversight → liability |

## Success criteria (for implementation)

1. Wrong orientation is **detectable** (contradictions, low confidence) before irreversible Act.
2. Every consequential action is **traceable** (intent → decision context → outcome).
3. Fast path (IG&C) and full loop are **explicit, gated modes** — not accidental.
4. Humans have **structured** orientation checkpoints, not generic "approve/deny."

## Further reading

- [OODA Loop Architecture for Production AI Agents](https://superml.dev/ooda-loop-architecture-production-ai-agents-2026)
- [The OODA Loop: Boyd's decision-making framework](https://strategyu.co/ooda-loop/)
- [How AI and LLMs Are Reshaping the OODA Loop](https://carolinagal14.medium.com/how-ai-and-large-language-models-are-reshaping-the-ooda-loop-76353e5098de)
- [OODA Loops for Agentic AI in Enterprise Systems](https://www.kamiwaza.ai/insights/ooda-loops-for-agentic-ai-in-enterprise-systems)
