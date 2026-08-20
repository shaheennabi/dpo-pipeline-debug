# DPO Pipeline Debug

## Task idea

A large synthetic preference-data pipeline contains a silent record-selection bug. The task is designed to require systematic inspection of intermediate artifacts, quantitative hypothesis testing, repair of the first divergent transformation, and end-to-end verification.

## Fairness

The instruction specifies the required semantic outcome but does not disclose the defective invariant, affected IDs, or the repair. The visible dataset is large enough that manual inspection is impractical; the hidden dataset contains unseen duplicate patterns. The verifier is deterministic and programmatic.

## Verifier

`tests/grader.py` independently reconstructs the expected representative-selection behavior from raw data, checks the candidate's visible output, directly exercises the candidate implementation on hidden data, and checks the required report. No LLM judge is used.

## Provenance

All task logic and synthetic records were created for this exercise. No direct port of SWE-bench, Terminal-Bench, a public CTF, a public issue, a Kaggle task, or another benchmark is used.

## Reproduction

```bash
harbor run -p ./dpo-pipeline-debug -a oracle
harbor run -p ./dpo-pipeline-debug -a &lt;agent&gt; -m &lt;gpt-5.5-high-or-opus-4.7&gt;
harbor view ./jobs