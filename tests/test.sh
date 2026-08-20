#!/usr/bin/env bash
set -euo pipefail
TEST_ROOT=/tests
SOLUTION_ROOT=/solution
mkdir -p "$SOLUTION_ROOT/data" /data /logs/verifier
cp "$TEST_ROOT/data/raw_preferences.jsonl" /data/raw_preferences.jsonl
python "$TEST_ROOT/src/parse.py"
cp "$TEST_ROOT/data/parsed_preferences.jsonl" "$SOLUTION_ROOT/data/parsed_preferences.jsonl"
python "$TEST_ROOT/src/normalize.py"
cp "$TEST_ROOT/data/normalized_preferences.jsonl" "$SOLUTION_ROOT/data/normalized_preferences.jsonl"
python "$SOLUTION_ROOT/src/dedup.py"
python "$SOLUTION_ROOT/src/format.py"

# Run grader; capture exit code so we always produce a reward file
RC=0
python "$TEST_ROOT/grader.py" || RC=$?

# Ensure reward file exists even if grader crashed
if [ ! -f /logs/verifier/reward.json ]; then
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