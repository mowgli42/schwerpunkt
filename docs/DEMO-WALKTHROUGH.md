# Operator Demo Walkthrough

Headless or browser demo of Boyd OODA **manual mode** — operators perform Orient and Decide; no LLM or MCP required.

## Prerequisites

```bash
cd schwerpunkt
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Option A: CLI (unattended / CI-friendly)

```bash
chmod +x scripts/demo-manual.sh
./scripts/demo-manual.sh
```

Steps performed:

1. Create manual session with `contradiction_case` fixture
2. Load observe signals (closed case in world model, open signal from API)
3. Advance → **pause at Orient** (contradiction)
4. Operator resolves `case_status` → `open`
5. Advance → **pause at Decide** (pick candidate)
6. Operator selects candidate A (Investigate)
7. Act executes; audit trail records intent/outcome

## Option B: Browser console

```bash
export SCHWERKPUNKT_MODE=manual
export SCHWERKPUNKT_PROFILE=local
uvicorn schwerpunkt.api.app:app --reload
```

Open http://127.0.0.1:8000/console

1. Click **New session (contradiction_case)**
2. Click **Advance loop** → contradiction panel appears
3. Click **Resolve contradiction**
4. Click **Advance** → pick candidate → **Submit decision**
5. Review **Audit trail**

## Option C: Stub mode (automated verification)

```bash
pytest tests/ -q
npx @fission-ai/openspec validate --specs --strict
```

## Fixtures

| Scenario | File | Operator action |
|----------|------|-----------------|
| Contradiction | `fixtures/scenarios/contradiction_case.json` | Resolve `case_status` |
| IG&C fast path | `fixtures/scenarios/igc_retrieve.json` | None (auto bypass) |
| Risk budget | Create session with `risk_budget=0` | Observe escalation |

## Grok concept mapping

| Boyd phase | Demo behavior |
|------------|---------------|
| Observe | Fixture sensors inject signals |
| Orient | Operator resolves contradictions (schwerpunkt) |
| Decide | Operator picks candidate / approves irreversible |
| Act | System executes + audit intent/outcome |
| IG&C | Rule table bypass for `retrieve_status` in stub/manual |
