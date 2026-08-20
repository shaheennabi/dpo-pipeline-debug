#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "normalized_preferences.jsonl"
OUT_PATH = ROOT / "data" / "deduped_preferences.jsonl"


def deduplicate_records(path: Path) -> list[dict]:
    records = []

    with path.open("r", encoding="utf-8") as infile:
        for line in infile:
            if line.strip():
                records.append(json.loads(line))

    # Build a deterministic representative map.
    # Each normalized prompt maps to its most complete record.
    representative = {}
    for record in records:
        key = record["_prompt_key"]
        representative[key] = record

    # Emit one record per prompt, preserving the original source order
    # of first appearance for stable downstream processing.
    seen = set()
    unique = []

    for record in records:
        key = record["_prompt_key"]

        if key in seen:
            continue

        seen.add(key)
        unique.append(representative[key])

    return unique


def main():
    records = deduplicate_records(IN_PATH)

    with OUT_PATH.open("w", encoding="utf-8") as outfile:
        for record in records:
            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Kept {len(records)} unique preference records at {OUT_PATH}")


if __name__ == "__main__":
    main()