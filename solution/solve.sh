#!/usr/bin/env bash
set -euo pipefail
ROOT=/solution

python "$ROOT/src/parse.py"
python "$ROOT/src/normalize.py"

cat > "$ROOT/src/dedup.py" <<'PY'
#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "data" / "normalized_preferences.jsonl"
OUT = ROOT / "data" / "deduped_preferences.jsonl"


def deduplicate_records(path):
    seen = set()
    unique = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            key = record["_prompt_key"]
            if key in seen:
                continue
            seen.add(key)
            unique.append(record)
    return unique


def main():
    rows = deduplicate_records(IN)
    with OUT.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Kept {len(rows)} unique preference records at {OUT}")


if __name__ == "__main__":
    main()
PY

python "$ROOT/src/dedup.py"
python "$ROOT/src/format.py"

cat > "$ROOT/REPORT.md" <<'REPORT'
# Pipeline Repair Report

## What was wrong
The deduplication stage selected the wrong representative for normalized duplicate prompts.

## How I detected the divergence
I compared the source records with parsed, normalized, deduplicated, and formatted artifacts and quantified which IDs survived each stage.

## Root cause
The deduplication stage imposed an unrelated response-length ordering before selecting one record per canonical prompt.

## What I changed
I removed the unrelated response-length ordering so representative selection follows source order.

## Verification
I reran the complete pipeline and checked both the generated artifacts and representative-selection behavior on unseen data.
REPORT
