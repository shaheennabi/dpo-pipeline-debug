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

    records.sort(
        key=lambda r: (
            r["_prompt_key"],
            -len(r["chosen"]),
            r["_source_index"],
        )
    )

    seen = set()
    unique = []

    for record in records:
        key = record["_prompt_key"]

        if key in seen:
            continue

        seen.add(key)
        unique.append(record)

    return unique


def main():
    records = deduplicate_records(IN_PATH)

    with OUT_PATH.open("w", encoding="utf-8") as outfile:
        for record in records:
            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Kept {len(records)} unique preference records at {OUT_PATH}")


if __name__ == "__main__":
    main()