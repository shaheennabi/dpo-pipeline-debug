#!/usr/bin/env bash
set -euo pipefail

TEST_ROOT="/tests"
SOLUTION_ROOT="/solution"

test -f "$TEST_ROOT/src/parse.py"
test -f "$TEST_ROOT/grader.py"
test -f "$TEST_ROOT/data/raw_preferences.jsonl"

test -f "$SOLUTION_ROOT/src/dedup.py"
test -f "$SOLUTION_ROOT/src/format.py"

mkdir -p "$SOLUTION_ROOT/data"
mkdir -p /data

cp "$TEST_ROOT/data/raw_preferences.jsonl" /data/raw_preferences.jsonl

python "$TEST_ROOT/src/parse.py"

cp "$TEST_ROOT/data/parsed_preferences.jsonl" \
   "$SOLUTION_ROOT/data/parsed_preferences.jsonl"

python "$SOLUTION_ROOT/src/dedup.py"
python "$SOLUTION_ROOT/src/format.py"

RC=0
python "$TEST_ROOT/grader.py" || RC=$?

mkdir -p /logs/verifier

if [ "$RC" -eq 0 ]; then
    cat > /logs/verifier/reward.json <<'JSON'
{
  "overall": 1.0,
  "functional_correctness": 1.0,
  "constraint_satisfaction": 1.0,
  "robustness": 1.0,
  "artifact_quality": 1.0
}
JSON
else
    cat > /logs/verifier/reward.json <<'JSON'
{
  "overall": 0.0,
  "functional_correctness": 0.0,
  "constraint_satisfaction": 0.0,
  "robustness": 0.0,
  "artifact_quality": 0.0
}
JSON
fi

exit "$RC"