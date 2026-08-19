#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw_preferences.jsonl"
OUT_PATH = ROOT / "data" / "parsed_preferences.jsonl"


def validate_record(record):
    required = {"id", "prompt", "chosen", "rejected"}
    if set(record.keys()) != required:
        raise ValueError(f"Record missing expected keys: {record}")
    for key in ("id", "prompt", "chosen", "rejected"):
        value = record[key]
        if not isinstance(value, str):
            raise TypeError(f"Field {key!r} in record {record.get('id')} is not a string.")
    if not record["id"].strip() or not record["prompt"].strip():
        raise ValueError(f"Record {record.get('id')} has an empty id or prompt.")
    return record


def parse_raw_preferences(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as infile:
        for lineno, line in enumerate(infile, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {lineno}: {exc}") from exc
            records.append(validate_record(record))
    return records


def main():
    records = parse_raw_preferences(RAW_PATH)
    with OUT_PATH.open("w", encoding="utf-8") as outfile:
        for record in records:
            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Parsed {len(records)} preference records to {OUT_PATH}")


if __name__ == "__main__":
    main()
