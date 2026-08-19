#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw_preferences.jsonl"
DEDUP_PATH = ROOT / "data" / "deduped_preferences.jsonl"
FINAL_PATH = ROOT / "data" / "final_preferences.jsonl"
# Hidden preferences are baked into the verifier image at /tests/hidden_preferences.jsonl
# (separate-verifier mode). Do not attempt host mounts or env vars here.
HIDDEN_PATH = Path('/tests/hidden_preferences.jsonl')
if not HIDDEN_PATH.exists():
    raise RuntimeError(
        "Hidden preference data not found inside verifier image at /tests/hidden_preferences.jsonl"
    )

MAX_RESPONSE_LENGTH = 180


def truncate_response(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_module_from_path(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def check_record_semantics(record: dict, expected_label: str):
    # Prefer the artifact-provided formatter from the agent (/solution), then common locations.
    candidates = [Path('/solution/src/format.py'), Path('/src/format.py'), ROOT / 'src' / 'format.py', Path('/tests/src/format.py')]
    format_path = None
    for p in candidates:
        if p.exists():
            format_path = p
            break
    if format_path is None:
        raise RuntimeError(f"Formatter module not found in any expected location: {candidates}")

    format_module = load_module_from_path(format_path, "format_module")
    formatted = format_module.format_record(record, MAX_RESPONSE_LENGTH)
    expected_chosen = truncate_response(record["chosen"], MAX_RESPONSE_LENGTH)
    expected_rejected = truncate_response(record["rejected"], MAX_RESPONSE_LENGTH)

    if formatted["chosen"] != expected_chosen or formatted["rejected"] != expected_rejected:
        raise AssertionError(
            f"Corruption detected for {record['id']} in {expected_label}. "
            f"Expected chosen={expected_chosen!r}, rejected={expected_rejected!r}; got "
            f"chosen={formatted['chosen']!r}, rejected={formatted['rejected']!r}."
        )


def check_pipeline_output():
    final_rows = load_jsonl(FINAL_PATH)
    dedup_rows = load_jsonl(DEDUP_PATH)
    final_by_id = {row["id"]: row for row in final_rows}

    for record in dedup_rows:
        row = final_by_id.get(record["id"])
        if row is None:
            raise AssertionError(f"Missing record {record['id']} in final output.")
        expected_chosen = truncate_response(record["chosen"], MAX_RESPONSE_LENGTH)
        expected_rejected = truncate_response(record["rejected"], MAX_RESPONSE_LENGTH)
        if row["chosen"] != expected_chosen or row["rejected"] != expected_rejected:
            raise AssertionError(
                f"Final output is corrupted for {record['id']}. "
                f"Expected chosen={expected_chosen!r}, rejected={expected_rejected!r}; got "
                f"chosen={row['chosen']!r}, rejected={row['rejected']!r}."
            )


def main():
    dedup_rows = load_jsonl(DEDUP_PATH)
    hidden_rows = load_jsonl(HIDDEN_PATH)

    for record in dedup_rows:
        check_record_semantics(record, "deduplicated pipeline data")
    for record in hidden_rows:
        check_record_semantics(record, "hidden verification data")

    check_pipeline_output()
    print("Pipeline semantics preserved for deduplicated and hidden preference data.")


if __name__ == "__main__":
    main()
