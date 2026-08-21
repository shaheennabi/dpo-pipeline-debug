# Task

Some preference records in the final export are incorrect.

Investigate the repository and its complete data-processing pipeline, determine where the first semantic divergence from the source data appears, repair the underlying cause, and regenerate the final dataset.

Requirements:

- Preserve legitimate source data.
- Do not delete records merely to make the output pass.
- Do not hard-code corrections for individual IDs or examples.
- The fix must generalize to preference data that is not present in the supplied examples.
- Preserve the existing pipeline structure unless a change is necessary to repair the underlying issue.
- Deduplication must retain exactly one record per normalized prompt: the record from the **first** occurrence in source order. Do not select a "best" or "most complete" duplicate — retained content and identity (including `id`) must match the first-seen record exactly.
- Prompt normalization for deduplication purposes must be case-insensitive, must collapse internal whitespace, and must ignore trailing punctuation (one or more of `. , ! ? ; :` at the end of the prompt, after whitespace is trimmed). Two prompts that differ only by trailing punctuation (e.g. `"Explain X"` vs `"Explain X?"`) must be treated as the same prompt and deduplicated accordingly.

The dataset is intentionally large enough that inspection should be systematic rather than manual. Compare intermediate artifacts, use scripts to quantify patterns, form and test hypotheses, and verify the repaired pipeline end to end.

Produce `REPORT.md` explaining:

- what was wrong
- how you located the first divergence
- the root cause
- what you changed
- how you verified the fix

Run the complete pipeline after making the repair. Verify both the generated dataset and the general behavior of the repaired code.