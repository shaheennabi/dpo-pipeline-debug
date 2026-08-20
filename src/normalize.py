#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "parsed_preferences.jsonl"
OUT_PATH = ROOT / "data" / "normalized_preferences.jsonl"


def normalize_prompt(prompt: str) -> str:
    return " ".join(prompt.strip().split()).lower()


def main():
    rows = []

    with IN_PATH.open("r", encoding="utf-8") as infile:
        for line in infile:
            if not line.strip():
                continue

            record = json.loads(line)
            record["_prompt_key"] = normalize_prompt(record["prompt"])
            rows.append(record)

    with OUT_PATH.open("w", encoding="utf-8") as outfile:
        for record in rows:
            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Normalized {len(rows)} preference records to {OUT_PATH}")


if __name__ == "__main__":
    main()