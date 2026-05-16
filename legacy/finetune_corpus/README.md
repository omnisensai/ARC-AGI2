# Fine-tuning corpus

Per-attempt records of `def solve()` code, grouped by failure mode. Built
automatically every time `paste_helper.py` processes an iter, and backfilled
from existing `Model Results/` and `research/true_solves/` via
`backfill_finetune_corpus.py`.

## Buckets

| File | Meaning | Volume signal |
|---|---|---|
| `wrong_training.jsonl` | Code that fails ≥1 training pair. Easy to mine. Teaches "this doesn't even generalize across the visible examples." | Highest |
| `wrong_test.jsonl` | Code that passes all training pairs but is wrong on test (NEAR_MISS or FALSE_CONFIDENT_SUBMIT). Rare and high-value — the model overfit the training rule. | Lowest, most valuable |
| `correct.jsonl` | TRUE_SOLVE: training pass + test exact. | Sparse, sample-efficient |

## Per-puzzle mirrors

`by_puzzle/<puzzle_id>/<bucket>.py` concatenates every record for one puzzle
into a single Python file, with metadata in comment headers. Lets a human
scan all the wrong attempts on one puzzle side-by-side without parsing
JSONL.

## Record schema

```json
{
  "puzzle_id": "13e47133",
  "model": "GPT",
  "iter": 1,
  "label": "wrong_training",
  "training_pass": 2,
  "training_total": 3,
  "training_diff_total": 26,
  "test_diff_total": null,
  "test_label": null,
  "stated_rule": "the rule sentence the model wrote, or null",
  "code": "def solve(input_grid):\n  ...",
  "source": "Model Results/GPT/13e47133/iter_1_response.py"
}
```

`iter=0` is reserved for canonical curated solvers under
`research/true_solves/` (those don't come from a paste iter so they get a
sentinel index).

## Idempotency

Each record is keyed on `(puzzle_id, model, iter)`. Re-running paste_helper
or the backfill replaces the prior record rather than duplicating it. If a
record's label changes (rare — e.g., the same iter was previously labeled
wrong_training but is now correct after a re-run), the record migrates: the
new bucket gets it and all other buckets drop the matching key.

## Comp-clean

`test_diff_total` is only computed when the puzzle file carries
`test[i].output`. In real competition that field is absent and the corpus
silently skips appending — there's no leak path from test ground truth into
prompts. The corpus is a post-hoc training artifact, not a feedback signal.

## DPO / preference pairs

For preference learning, pair `correct` with `wrong_test` on the **same
puzzle**. Same puzzle = same prompt, so the difference between the
preferred and rejected completion is entirely in the code, which is what
the model should learn to distinguish.

Training-fail pairs (`correct` vs `wrong_training`) are usable too but the
distinction is coarser — the wrong code fails for obvious reasons (didn't
even pass the visible examples), so the preference signal is weaker.
