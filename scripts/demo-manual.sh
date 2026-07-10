#!/usr/bin/env bash
# Headless manual demo — no browser, no LLM, no MCP
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then PYTHON=python3; fi

export SCHWERKPUNKT_MODE=manual
export SCHWERKPUNKT_PROFILE=local
export SCHWERKPUNKT_DATA_DIR="${TMPDIR:-/tmp}/schwerpunkt-demo-$$"
mkdir -p "$SCHWERKPUNKT_DATA_DIR"

echo "==> Starting contradiction_case manual demo"
OUT=$("$PYTHON" -m schwerpunkt.cli.main session start --mode manual --profile local --scenario contradiction_case)
SID=$(echo "$OUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
echo "Session: $SID"

"$PYTHON" -m schwerpunkt.cli.main session load --id "$SID" --scenario contradiction_case
"$PYTHON" -m schwerpunkt.cli.main session run --id "$SID" --scenario contradiction_case

echo "==> Resolving contradiction (operator step)"
"$PYTHON" -m schwerpunkt.cli.main session resolve --id "$SID" --fact-key case_status --value open --rationale "supervisor reopened"

"$PYTHON" -m schwerpunkt.cli.main session run --id "$SID"
"$PYTHON" -m schwerpunkt.cli.main session decide --id "$SID" --candidate A
"$PYTHON" -m schwerpunkt.cli.main session run --id "$SID"

LOOP=$("$PYTHON" -c "import json,sqlite3,os; c=sqlite3.connect(os.environ['SCHWERKPUNKT_DATA_DIR']+'/schwerpunkt.db'); r=c.execute('select payload from sessions where id=?',('$SID',)).fetchone(); print(json.loads(r[0])['world_model']['loop_count'])" 2>/dev/null || echo 0)
echo "==> Demo complete for session $SID (loop_count=$LOOP)"
