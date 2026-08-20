#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "deduped_preferences.jsonl"
OUT_PATH = ROOT / "data" / "final_preferences.jsonl"
MAX_RESPONSE_LENGTH = 180


def truncate_response(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def format_record(record: dict, max_length: int) -> dict:
    return {
        "id": record["id"],
        "prompt": record["prompt"],
        "chosen": truncate_response(record["chosen"], max_length),
        "rejected": truncate_response(record["rejected"], max_length),
    }


def main():
    rows = []

    with IN_PATH.open("r", encoding="utf-8") as infile:
        for line in infile:
            if line.strip():
                rows.append(format_record(json.loads(line), MAX_RESPONSE_LENGTH))

    with OUT_PATH.open("w", encoding="utf-8") as outfile:
        for row in rows:
            outfile.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Formatted {len(rows)} preference records to {OUT_PATH}")


if __name__ == "__main__":
    main()