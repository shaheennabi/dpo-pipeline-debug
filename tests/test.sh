#!/usr/bin/env bash
set -euo pipefail
TEST_ROOT=/tests
SOLUTION_ROOT=/solution
mkdir -p "$SOLUTION_ROOT/data" /data
cp "$TEST_ROOT/data/raw_preferences.jsonl" /data/raw_preferences.jsonl
python "$TEST_ROOT/src/parse.py"
cp "$TEST_ROOT/data/parsed_preferences.jsonl" "$SOLUTION_ROOT/data/parsed_preferences.jsonl"
python "$TEST_ROOT/src/normalize.py"
cp "$TEST_ROOT/data/normalized_preferences.jsonl" "$SOLUTION_ROOT/data/normalized_preferences.jsonl"
python "$SOLUTION_ROOT/src/dedup.py"
python "$SOLUTION_ROOT/src/format.py"
python "$TEST_ROOT/grader.py"
mkdir -p /logs/verifier
cp "$TEST_ROOT/reward.json" /logs/verifier/reward.json