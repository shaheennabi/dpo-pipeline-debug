# DPO Pipeline Debug

This repository contains a minimal synthetic preference-data pipeline used to test whether a long-horizon coding agent can diagnose and repair a silent data-corruption bug.

The pipeline is intentionally small and self-contained:

- `data/raw_preferences.jsonl`: raw preference pairs
- `src/parse.py`: validate and normalize raw records
- `src/dedup.py`: remove duplicate prompts deterministically
- `src/format.py`: format/truncate responses for export

Your goal is to investigate the repository, identify the root cause, repair the bug, and restore the original preference semantics.
