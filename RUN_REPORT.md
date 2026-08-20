# Run Report

## Task design

The task uses a 2,500-record visible preference dataset with 300 normalized duplicate groups and a 400-record hidden dataset with 80 unseen duplicate groups. The planted defect is in representative selection during deduplication.

## Oracle

The Oracle solution removes the response-length ordering from the deduplication stage, reruns parse -> normalize -> dedup -> format, and writes `REPORT.md`. The verifier independently expects first source occurrence per normalized prompt.

## Verification status

The finalized task was locally exercised end to end: 2,500 visible records produced 2,200 deduplicated and final records; the independent verifier returned full scores for functional correctness, constraint satisfaction, robustness, and artifact quality.

## Target-model evidence

Target-model evidence must be collected on this finalized revision after the Oracle passes on the evaluator machine.
