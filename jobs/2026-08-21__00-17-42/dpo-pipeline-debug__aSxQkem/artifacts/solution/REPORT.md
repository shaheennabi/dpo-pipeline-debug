# Preference Pipeline Repair Report

## What was wrong

The final export contained incorrect preference representatives for duplicated prompts. The pipeline is supposed to collapse records with the same normalized prompt to one representative, choosing the most complete preference pair. Instead, `src/dedup.py` always overwrote the representative for a prompt as records were read, so the last duplicate won even when an earlier duplicate had the more complete `chosen` and `rejected` responses.

## How I located the first divergence

I regenerated and compared every pipeline stage:

- `parse.py` preserved all 2,500 raw records and added `_source_index`; mismatches with raw source fields: 0.
- `normalize.py` preserved all parsed source fields and added the expected `_prompt_key`; malformed or mismatched normalized rows: 0.
- The raw/normalized data contained 2,200 normalized prompt keys. Of those, 300 prompt groups were duplicates, all pairs.
- The old dedup output exactly matched "last duplicate wins".
- Comparing duplicate representatives against a "most complete, earliest tie" rule showed 215 dedup representative divergences. Because parse and normalize had no semantic mismatches, the first semantic divergence appeared in `dedup.py`.

The duplicate groups were systematic: 150 groups had unequal response completeness, and 150 groups were exact duplicate preference pairs. The old last-wins rule selected the wrong representative whenever the earlier record was more complete or when an equal duplicate should have kept source-order determinism.

## Root cause

`src/dedup.py` built `representative` like this:

```python
for record in records:
    key = record["_prompt_key"]
    representative[key] = record
```

That ignored the intended "most complete record" behavior described by the stage comment. It made representative selection depend only on file position among duplicates, not on preference content.

## What changed

I added a `response_completeness()` helper in `src/dedup.py` and changed representative selection to:

- score each record by the number of non-empty preference responses and the combined stripped length of `chosen` plus `rejected`;
- keep the first record for a prompt initially;
- replace it only when a later duplicate has a strictly better completeness score;
- keep ties as the earlier source record.

This preserves legitimate source rows, keeps one output record per normalized prompt, preserves first-prompt output ordering, and generalizes to unseen duplicate groups without hard-coded IDs.

## Verification

I ran the complete pipeline:

```bash
python3 src/parse.py
python3 src/normalize.py
python3 src/dedup.py
python3 src/format.py
```

Results after repair:

- raw, parsed, normalized counts: 2,500 each.
- deduped and final counts: 2,200 each.
- parse mismatches against raw source fields: 0.
- normalize mismatches against parsed fields and prompt-key calculation: 0.
- dedup representatives not matching the repaired completeness rule: 0.
- final IDs match dedup IDs in order: true.
- final records contain only `id`, `prompt`, `chosen`, and `rejected`.
- 215 duplicate groups changed away from the old last-wins behavior.

I also compiled the Python stages with `python3 -m py_compile` and directly exercised `deduplicate_records()` on a synthetic duplicate fixture covering:

- earlier record more complete than later duplicate;
- later record more complete than earlier duplicate;
- equal-completeness tie preserving the first record;
- a long partial record losing to a shorter complete preference pair.
