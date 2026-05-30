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

## Kickoff (RunPod H100 SXM)

After `bash "Fine Tune Run 2/train_preflight.sh"` finishes clean:

```bash
cd /workspace/ARC-AGI2
git pull origin claude/gifted-mayer-3ITc1

# 1. Convert SFT records to axolotl chat format + held-out filter (defensive)
python3 Phase2_V2/run1/prepare_dataset.py
# -> Phase2_V2/run1/data_sft/run1_train.jsonl.gz   (~4 MB gzipped, 31,726 records)

# 2. Dry-run the YAML (catches schema/template errors in ~1 min)
axolotl preprocess Phase2_V2/run1/run1_axolotl.yaml

# 3. Train (the actual job — H100 SXM 80GB, ~5-6 hours for 3 epochs)
axolotl train Phase2_V2/run1/run1_axolotl.yaml 2>&1 | tee outputs/phase2_v2_run1/train.log
```

After training: `outputs/phase2_v2_run1/` holds the LoRA checkpoint.
Then run eval:

```bash
python3 Phase2_V2/run1/eval_harness.py \
    --lora outputs/phase2_v2_run1 --bucket 1
python3 Phase2_V2/run1/eval_harness.py \
    --lora outputs/phase2_v2_run1 --bucket 2 --augment
python3 Phase2_V2/run1/eval_harness.py \
    --lora outputs/phase2_v2_run1 --bucket 3 --augment
python3 Phase2_V2/run1/eval_harness.py --report
```

(Eval harness's `model_emit` is the deferred glue — wire it to vLLM or HF
`.generate` in the eval environment.)

### Tips from the runbook (see `Fine Tune Run 2/RUNBOOK.md` §2.5)

- If flash-attn compile fails: set `flash_attention: false` in the yaml. H100 80GB has plenty of memory without it.
- If you regenerate the dataset later: `rm -rf Phase2_V2/run1/data_sft/prepared/run1` to invalidate axolotl's stale tokenized cache.
- If `axolotl train` says "Template 'qwen2' not found": already fixed — we use `tokenizer_default`.
- HF cache lives on `/workspace/hf_cache` (not the 20GB overlay).
