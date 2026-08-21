# RUN_REPORT.md — dpo-pipeline-debug

## 1. Task idea

A synthetic 4-stage DPO preference-data pipeline (`parse.py → normalize.py → dedup.py → format.py`)
over a 2,500-row raw preference dataset. A silent bug is planted in `dedup.py`: the
`representative` map is built by unconditional overwrite (`representative[key] = record`),
so duplicate prompt groups retain the **last**-seen record's content while the output is
emitted in **first**-seen order. This produces mismatched id/content pairs in the deduplicated
and final output without any crash, exception, or malformed JSON — the pipeline runs cleanly
and produces plausible-looking output.

The agent must inspect all four pipeline stages, quantify the divergence (not eyeball it — the
dataset is large enough that this requires scripting), localize the true root cause in `dedup.py`,
repair it so behavior matches the specified contract (retain the first-seen record exactly,
content and id), rerun the full pipeline, and produce a written report of its process.

## 2. Provenance

Created from scratch for this exercise. No external dataset, benchmark, or prior task was
ported or adapted. Synthetic preference data was generated programmatically; the pipeline
code and planted bug are original.

## 3. Long-horizon structure

- 4 linked pipeline stages, each depending on the previous stage's output.
- 2,500-row visible dataset — large enough that manual inspection does not scale; the agent
  must write and run its own analysis/comparison scripts to find the divergence pattern.
- A held-out hidden dataset (not visible to the agent) used only by the verifier, to reject
  fixes that memorize or hardcode against the visible data rather than generalizing.
- Required deliverable: a corrected `dedup.py`, a regenerated dataset, and a written
  root-cause report — not just a passing test.

## 4. Verifier design

`tests/grader.py` checks, independently of any LLM judge:

1. **Visible correctness** — the submitted `dedup.py`'s output on the visible dataset matches
   exact expected content and ordering (first-occurrence retention).
2. **Hidden-data robustness** — the submitted `dedup.py` module is imported and run directly
   against a held-out dataset never shown to the agent; output must match expected content
   field-by-field (not just ID order — see §7, a bug found and fixed during our own validation).
3. **Constraint satisfaction** — row counts, structural integrity of output.
4. **Artifact quality** — presence and coherence of the submitted `REPORT.md`.

Reward is written to `/logs/verifier/reward.json` as a 4-field breakdown plus `overall`.
Overall `< 1.0` fails the trial.

### Anti-shortcut resistance validated locally

| Attack | Result |
|---|---|
| Oracle (correct fix) | `overall: 1.0` (all four sub-scores 1.0) |
| Negative control (bug left in place, oracle otherwise unchanged) | `overall: 0.5` (`functional_correctness: 0.0`, `constraint_satisfaction: 0.0`) |

The negative control confirms the verifier actually rejects a broken solution rather than
passing everything by default — this was explicitly tested, not assumed.

**Known verifier limitation:** `grader.py` returns early on visible-check failure, leaving
`robustness` and `artifact_quality` at their initialized default (`1.0`) rather than marking
them not-evaluated. This does not affect pass/fail (gated on `overall < 1.0`), but the
sub-score breakdown should not be read as "robustness/artifact quality were confirmed" when
`functional_correctness` is `0.0`. Documented here rather than hidden.

## 5. Oracle result

```
harbor run -p . -a oracle --force-build
```
```json
{"overall": 1.0, "functional_correctness": 1.0, "constraint_satisfaction": 1.0, "robustness": 1.0, "artifact_quality": 1.0}
```

## 6. Target model run

```
harbor run -p . -a codex -m openai/gpt-5.5-pro \
  --ae OPENAI_API_KEY=$env:OPENROUTER_API_KEY \
  --ae OPENAI_BASE_URL=https://openrouter.ai/api/v1 \
  --ak reasoning_effort=high
```

Result:
```json
{"overall": 0.5, "functional_correctness": 0.0, "constraint_satisfaction": 0.0, "robustness": 1.0, "artifact_quality": 1.0}
```
(`robustness`/`artifact_quality` at default per the early-return behavior noted in §4 — not
independently confirmed for this run.)

## 7. Failure analysis

**Verifier evidence:**
```
AssertionError: visible dedup: mismatch at row 5, field id, candidate id=p0201-dup, expected id=p0201
```

**What the model did:** GPT-5.5-pro correctly localized the fault to `dedup.py`'s
`representative` map and correctly identified the unconditional-overwrite pattern as
suspicious. It systematically compared all four pipeline stages and quantified the divergence
(2,500 raw rows, 2,200 unique prompt keys, 300 duplicate groups, 215 representative
divergences under its own proposed rule) — this part of its process was genuinely thorough
and matches the long-horizon behavior the task is designed to require.

Where it went wrong: rather than implementing strict first-occurrence retention, it built a
`response_completeness()` heuristic that selects whichever duplicate has more non-empty /
longer `chosen` and `rejected` fields, and cited a comment in the seed code
(`# Each normalized prompt maps to its most complete record`) as the basis for this design
choice. For the `p0201` / `p0201-dup` pair, its heuristic selected the longer duplicate as
representative, substituting a different record's `id` into a slot where the grader requires
the first-seen record's `id` to survive unchanged.

**Failure taxonomy:** primarily **wrong hypothesis** (the model inferred an incorrect
specification — "most complete" — for the deduplication rule) with a **skipped verification**
component (it validated its fix extensively against its own inferred rule, but never checked
that rule against the pipeline's literal, minimal contract before finishing).

**Important caveat on task fairness, disclosed transparently:** at the time of this run,
`instruction.md` did not explicitly specify first-occurrence-only semantics, and the seed
`dedup.py` contained a comment reading "most complete record" — the only textual signal in
the entire task pointing toward a specific rule, and it pointed toward the wrong one. GPT-5.5's
`REPORT.md` explicitly cites this comment as its basis. This is a legitimate task-design
ambiguity, not manufactured after the fact: we identified it during post-run analysis, and
corrected both `instruction.md` (now explicitly states first-occurrence retention, exact
content and id) and the misleading comment before finalizing this submission. [STATE HERE:
either "A rerun after this fix produced the same failure, strengthening confidence this
reflects a genuine capability gap rather than spec ambiguity" (if you rerun), or "Given time
constraints this run is reported with the ambiguity disclosed rather than rerun; the fix is
included in the submitted task for future reproduction" (if you do not).]

## 8. Fairness audit

- Solvable: oracle passes at 1.0 from the provided files with no modification.
- Unambiguous: instruction.md now explicitly states the exact deduplication contract (see §7).
- Substantive: failure stems from data/code forensics and specification inference under
  ambiguity resolved by the model's own (reasonable but incorrect) reading of in-repo text,
  not from brittle formatting or missing dependencies.
- Reproducible: no network required beyond initial agent-harness setup; hidden data isolated
  from the agent's build context (verified via direct image inspection — see reproduction
  commands).
- Non-brittle: verifier checks exact content/id correctness on both visible and held-out data,
  not string-matching or superficial output shape.

## 9. Reproduction commands

```
harbor run -p . -a oracle --force-build
harbor run -p . -a codex -m openai/gpt-5.5-pro \
  --ae OPENAI_API_KEY=$env:OPENROUTER_API_KEY \
  --ae OPENAI_BASE_URL=https://openrouter.ai/api/v1 \
  --ak reasoning_effort=high
harbor view ./jobs
```

## 10. Limitations

- `robustness`/`artifact_quality` sub-scores are not independently meaningful when
  `functional_correctness` is `0.0`, due to the grader's early-return design (§4).
- The instruction/comment ambiguity described in §7 was present during the reported run and
  was corrected afterward; this is disclosed rather than omitted.