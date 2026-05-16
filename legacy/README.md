# Legacy artifacts

Everything here predates the R/F naming refactor. Kept for reference and
potential corpus mining; **not** read or written by the current pipeline.

## Layout

| Path | Was |
|---|---|
| `legacy/Model Results/<Model>/<puzzle>/iter_N_*` | Per-iter artifacts under the old naming (iter 1 = first response, iter_N+1_fresh_refine_prompt was the next prompt, iter_N_feedback was the inspection dump). |
| `legacy/Pastes_processed/` | Old paste files using `<puzzle>__<model>__iter<N>.txt` (double-underscore) convention. |
| `legacy/finetune_corpus/` | Old corpus records with `iter` field keyed on the legacy naming. |

## New naming (going forward)

Inside `Model Results/<Model>/<puzzle>/`:

| File | Meaning |
|---|---|
| `R<N>.txt` | Raw paste of model's Nth response. R1 is the response to the seed prompt. R2 is the response to F1, and so on. |
| `R<N>.py` | Extracted `def solve()`. |
| `R<N>_rule.txt` | Extracted `STATED_RULE:` (R1) or `Updated rule (one sentence):` (R≥2). |
| `R<N>_hand_grid.json` | Extracted `TEST_OUTPUT`. |
| `R<N>_summary.json` | Verdict + training/test diff stats. |
| `R<N>_feedback.txt` | Inspection dump (legacy substrate + new diagnosis). |
| `F<N>.txt` | Feedback prompt → paste this into a fresh chat to produce R(N+1). |

`Pastes/<puzzle>_<model>[_R<N>].txt`. No suffix = R1 (seed response).
Workflow parses single-underscore tokens; ARC puzzle IDs are 8-char hex
so there's no collision risk.
