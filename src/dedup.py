#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "parsed_preferences.jsonl"
OUT_PATH = ROOT / "data" / "deduped_preferences.jsonl"


def normalize_prompt(prompt: str) -> str:
    return " ".join(prompt.strip().split()).lower()


def deduplicate_records(path: Path) -> list[dict]:
    seen = set()
    unique = []
    with path.open("r", encoding="utf-8") as infile:
        for line in infile:
            if not line.strip():
                continue
            record = json.loads(line)
            prompt_key = normalize_prompt(record["prompt"])
            if prompt_key in seen:
                continue
            seen.add(prompt_key)
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
