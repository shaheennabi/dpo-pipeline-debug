#!/usr/bin/env python3
import importlib.util
import json
import tempfile
from pathlib import Path

TEST_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ROOT = Path("/solution")

RAW_PATH = TEST_ROOT / "data" / "raw_preferences.jsonl"
DEDUP_PATH = CANDIDATE_ROOT / "data" / "deduped_preferences.jsonl"
FINAL_PATH = CANDIDATE_ROOT / "data" / "final_preferences.jsonl"
HIDDEN_PATH = Path("/tests/hidden_preferences.jsonl")

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


def normalize_prompt(prompt: str) -> str:
    return " ".join(prompt.strip().split()).lower()


def expected_dedup(records: list[dict]) -> list[dict]:
    seen = set()
    result = []

    for record in records:
        key = normalize_prompt(record["prompt"])

        if key in seen:
            continue

        seen.add(key)
        result.append(record)

    return result


def check_candidate_dedup_module(records: list[dict], label: str):
    module = load_module_from_path(
        CANDIDATE_ROOT / "src" / "dedup.py",
        f"candidate_dedup_{label}",
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".jsonl",
        delete=False,
    ) as fh:
        temp_path = Path(fh.name)
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    try:
        observed = module.deduplicate_records(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)

    expected = expected_dedup(records)

    if observed != expected:
        raise AssertionError(
            f"Candidate deduplication failed on {label} data.\n"
            f"Expected {len(expected)} records, got {len(observed)}."
        )


def check_formatter(records: list[dict], label: str):
    formatter = load_module_from_path(
        CANDIDATE_ROOT / "src" / "format.py",
        f"candidate_format_{label}",
    )

    for record in records:
        formatted = formatter.format_record(record, MAX_RESPONSE_LENGTH)

        expected_chosen = truncate_response(
            record["chosen"],
            MAX_RESPONSE_LENGTH,
        )
        expected_rejected = truncate_response(
            record["rejected"],
            MAX_RESPONSE_LENGTH,
        )

        if formatted["chosen"] != expected_chosen:
            raise AssertionError(
                f"Formatter changed chosen semantics for {record['id']} in {label}."
            )

        if formatted["rejected"] != expected_rejected:
            raise AssertionError(
                f"Formatter changed rejected semantics for {record['id']} in {label}."
            )

        if formatted["prompt"] != record["prompt"]:
            raise AssertionError(
                f"Formatter changed prompt for {record['id']} in {label}."
            )


def check_final_output(expected_deduped: list[dict]):
    final_rows = load_jsonl(FINAL_PATH)

    if len(final_rows) != len(expected_deduped):
        raise AssertionError(
            f"Final output length mismatch: "
            f"expected {len(expected_deduped)}, got {len(final_rows)}."
        )

    for observed, source in zip(final_rows, expected_deduped):
        expected = {
            "id": source["id"],
            "prompt": source["prompt"],
            "chosen": truncate_response(
                source["chosen"],
                MAX_RESPONSE_LENGTH,
            ),
            "rejected": truncate_response(
                source["rejected"],
                MAX_RESPONSE_LENGTH,
            ),
        }

        if observed != expected:
            raise AssertionError(
                f"Final output mismatch for {source['id']}.\n"
                f"Expected: {expected!r}\n"
                f"Observed: {observed!r}"
            )


def main():
    if not HIDDEN_PATH.exists():
        raise RuntimeError(
            "Hidden verification data missing from verifier."
        )

    raw_rows = load_jsonl(RAW_PATH)
    hidden_rows = load_jsonl(HIDDEN_PATH)
    expected_visible = expected_dedup(raw_rows)

    if not DEDUP_PATH.exists():
        raise AssertionError("Candidate deduped_preferences.jsonl missing.")

    if not FINAL_PATH.exists():
        raise AssertionError("Candidate final_preferences.jsonl missing.")

    candidate_dedup = load_jsonl(DEDUP_PATH)

    if candidate_dedup != expected_visible:
        raise AssertionError(
            "Candidate deduped output does not preserve "
            "the earliest normalized occurrence and source order."
        )

    check_candidate_dedup_module(hidden_rows, "hidden")

    check_formatter(expected_visible, "visible")
    check_formatter(hidden_rows, "hidden")

    check_final_output(expected_visible)

    print("All pipeline checks passed.")
    print(f"Visible raw records: {len(raw_rows)}")
    print(f"Expected retained records: {len(expected_visible)}")
    print(f"Hidden records tested: {len(hidden_rows)}")


if __name__ == "__main__":
    main()