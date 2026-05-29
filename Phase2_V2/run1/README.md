# Phase2_V2 / Run 1 — sealed plan

## What

ONE LoRA on the L2 same-size corpus only. No L1 micro, no diff-size, no
synthetic repair. Trains and evals only same-size; diff-size is **cold-probed**
to diagnose the gap.

## Numbers

| layer | records | source |
|---|---:|---|
| L2 original | 2,081 | `canonical/sft/real_samesize_original.jsonl` |
| L2 augmented | 29,645 | `canonical/sft/real_samesize_augmented_shard0[0-3].jsonl` |
| **Total** | **31,726** | over 739 unique puzzles |

Zero contamination: no held-out puzzle ids appear in any training file.

## Eval buckets

| # | name | puzzles | augmented (~) | purpose |
|---:|---|---:|---:|---|
| 1 | trained sample | 200 | n/a | "did it learn" sanity (~97% expected) |
| 2 | held-out same-size | 43 | ~640 | transfer signal + Phase 3 corpus |
| 3 | cold diff-size | 364 | ~5,500 | gap diagnosis + Phase 3 corpus |

Augmentation: 8 D4 × 5 color perms per puzzle, gate-filtered → ~15 accepted
per puzzle on average.

## Phase ordering (sealed)

1. **Train** Run 1 LoRA on the 31,726 same-size records.
2. **Eval** all three buckets (`eval_harness.py`).
3. **Collect failures** — each non-PASS becomes a Phase 3 record.
4. **Phase 3 repair**: DPO on (prompt, wrong-code, correct-code) pairs.
   Real failure distribution beats synthetic perturbations.

## Failure-mode taxonomy

The eval harness auto-classifies each prediction:

  - `PASS`            — exact match on test pair
  - `WRONG_OUTPUT`    — code runs, shape ok, cells wrong
  - `SHAPE_MISMATCH`  — output shape ≠ expected (key signal on bucket 3)
  - `RUNTIME_ERROR`   — code raised
  - `TIMEOUT`         — 3s wall cap exceeded
  - `EMPTY_OR_INVALID`— no `def solve`, syntax error
  - `HARDCODED`       — passes only by fingerprint / big literal / eq grid

Bucket 3's distribution across these modes drives the diff-size Phase 2 plan
(see playbook decision matrix).

## Files

  `train_config.py`       — LoRA hyperparams + data file list + held-out filter
  `eval_harness.py`       — bucket runner + classifier (LoRA `model_emit` is TODO)
  `splits/`               — bucket id lists
  `eval/`                 — eval output JSONL (populated by harness)
  `lora_out/`             — LoRA checkpoint dir (populated by trainer)

## Open: trainer driver

`train_config.py` is the spec; the actual `train.py` driver (transformers +
peft + datasets) lives outside this directory in whatever training environment
runs the job. The config exposes `load_heldout_ids()` so the dataloader can
filter at iter time.
