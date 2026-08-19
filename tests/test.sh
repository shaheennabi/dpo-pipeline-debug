#!/usr/bin/env bash
set -euo pipefail

# Locate repository root by checking common candidate paths for data/raw_preferences.jsonl
CANDIDATES=("$(pwd)" "/workspace" "/src" "/work" "/app" "/workdir" "/home" "/root")
ROOT=""
for c in "${CANDIDATES[@]}"; do
  if [ -f "$c/data/raw_preferences.jsonl" ]; then
    ROOT="$c"
    break
  fi
done

# Fallback to script-relative resolution
if [ -z "$ROOT" ] && [ -n "${BASH_SOURCE[0]:-}" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  ROOT="$(cd "$SCRIPT_DIR" && cd .. && pwd)"
fi

# Final fallback to current working dir
if [ -z "$ROOT" ]; then
  ROOT="$(pwd)"
fi

cd "$ROOT"

# Prefer /solution (agent copy), then /tests/src (uploaded tests), then repository src
if [ -d "/solution/src" ]; then
  SRC_ROOT="/solution/src"
elif [ -d "/tests/src" ]; then
  SRC_ROOT="/tests/src"
elif [ -d "$ROOT/src" ]; then
  SRC_ROOT="$ROOT/src"
else
  # fallback: search for parse.py in cwd
  PARSE_PATH="$(python - <<'PY'
from pathlib import Path
for f in Path('.').rglob('parse.py'):
    print(str(f))
    break
else:
    print('')
PY
)"
  if [ -z "$PARSE_PATH" ]; then
    echo "ERROR: could not locate parse.py" >&2
    exit 1
  fi
  SRC_ROOT="$(dirname "$PARSE_PATH")"
fi

python "$SRC_ROOT/parse.py"
python "$SRC_ROOT/dedup.py"
python "$SRC_ROOT/format.py"

# Ensure outputs are available at /data for grader expectations (grader resolves ROOT to /)
mkdir -p /data
if [ -d "/tests/data" ]; then
  cp -r /tests/data/* /data/ || true
fi

# Run verifier; if it exits non-zero the script will stop (set -e)
# Locate grader.py in common verifier locations (/tests, /solution/tests, $ROOT/tests, $ROOT)
if [ -f "/tests/grader.py" ]; then
  GRADER_PATH="/tests/grader.py"
elif [ -f "/solution/tests/grader.py" ]; then
  GRADER_PATH="/solution/tests/grader.py"
elif [ -f "$ROOT/tests/grader.py" ]; then
  GRADER_PATH="$ROOT/tests/grader.py"
elif [ -f "$ROOT/grader.py" ]; then
  GRADER_PATH="$ROOT/grader.py"
else
  echo "ERROR: could not locate grader.py" >&2
  exit 1
fi
# Run grader and map its exit code to a canonical reward written where Harbor collects it
python "$GRADER_PATH"
RC=$?
# Ensure verifier logs dir exists
mkdir -p /logs/verifier
if [ "$RC" -eq 0 ]; then
  # success -> use grader's produced reward if present, otherwise full scores
  if [ -f /tests/reward.json ]; then
    cp /tests/reward.json /logs/verifier/reward.json
    echo "Copied grader reward to /logs/verifier/reward.json"
    exit 0
  fi
  cat > /logs/verifier/reward.json <<'JSON'
{
  "overall": 1.0,
  "functional_correctness": 1.0,
  "constraint_satisfaction": 1.0,
  "robustness": 1.0,
  "artifact_quality": 1.0
}
JSON
  echo "Wrote /logs/verifier/reward.json (success)"
  exit 0
else
  # failure -> if grader produced a reward file, copy it; otherwise write zero score
  if [ -f /tests/reward.json ]; then
    cp /tests/reward.json /logs/verifier/reward.json
    echo "Copied grader reward to /logs/verifier/reward.json (failure)"
    exit $RC
  fi
  cat > /logs/verifier/reward.json <<'JSON'
{
  "overall": 0.0,
  "functional_correctness": 0.0,
  "constraint_satisfaction": 0.0,
  "robustness": 0.0,
  "artifact_quality": 0.0
}
JSON
  echo "Wrote /logs/verifier/reward.json (failure)"
  exit $RC
fi
