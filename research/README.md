# research/ — corpus directory

This directory does not get populated until `paste_helper.py` is run with the
`--label` flag and a training-pass-rate of 1.0 is achieved. It is the corpus
of labeled outcomes used for offline learning and detector calibration.

## Layout (auto-created on first labeled outcome)

```
research/
├── true_solves/
│   └── <puzzle_id>__<model>__iter<N>.py        # winning code, exact copy
│
├── near_misses/
│   └── <puzzle_id>__<model>__iter<N>/
│       ├── code.py                              # near-correct code
│       ├── test_diff.json                       # which cells differ from ground truth
│       └── error_pattern.json                   # signals for detector mining
│
├── false_confident_submits/
│   └── <puzzle_id>__<model>__iter<N>/
│       ├── code.py                              # training-passed, test-wrong code
│       ├── test_diff.json
│       └── error_pattern.json                   # most valuable for new detectors
│
├── bug_fixes/
│   └── <bug_class>/
│       └── <puzzle_id>__<model>__iter<N-1>_to_<N>/
│           ├── before.py
│           ├── after.py
│           ├── feedback.txt                     # what we showed the model
│           ├── diff.patch                       # before -> after
│           └── meta.json                        # bug_class, scores, signals
│
└── calibration/
    └── outcomes.csv                              # one row per submit-eligible attempt
```

## What gets labeled

When `paste_helper.py --label` runs and `training_pass_rate == 1.0`,
`research_mode.label_outcome()` runs `solve(test_input)` against the test
ground truth (research mode only — never read during the iteration loop)
and emits one of:

| Label | Meaning |
|---|---|
| `TRUE_SOLVE` | test exactly matches ground truth (0 cells wrong) |
| `NEAR_MISS` | 1 ≤ cells wrong ≤ 20 |
| `FALSE_CONFIDENT_SUBMIT` | > 20 cells wrong despite training all passing |

## How the corpus is used

- **true_solves/** — canonical solver code per puzzle. Regression test base.
- **false_confident_submits/** — most valuable. Each entry is a candidate
  spatial pattern for a new bug-class detector. Inspect manually; if you
  see a repeating pattern across multiple FALSE_CONFIDENT cases, write a
  detector matching that pattern (see constitution "bug-class library
  principle").
- **bug_fixes/** — paired `(buggy_code, feedback, fixed_code)` examples,
  organized by bug class. Future fine-tune dataset for "given feedback X
  on buggy code Y, produce fixed code Z."
- **calibration/outcomes.csv** — single source of truth for "does our
  cell-correctness threshold predict TRUE_SOLVE?" One row per labeled
  outcome with all phase-classifier signals.

## Bootstrapping the corpus from prior runs

If you have existing `Model Results/` data that was never labeled,
`backfill_research_corpus.py` walks all iters and applies the same labeling
retroactively:

```
python backfill_research_corpus.py
```

Idempotent — safe to re-run after adding new evaluation puzzles or new
detectors.

## Competition vs research distinction

In competition mode (no `--label` flag), the test ground truth is never
accessed. `research/` stays empty.

In research mode (`--label`), test ground truth is read only AFTER
training pass rate hits 1.0, only for the post-submit labeling step.
The labels never feed back into the iteration loop.

See `CONSTITUTION.md` for the full design.
