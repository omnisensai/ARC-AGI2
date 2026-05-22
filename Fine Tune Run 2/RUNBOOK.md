# Phase 1 Runbook — Training Pipeline Execution

Operational handoff for executing Run 2 Phase 1. Procedural only —
strategy lives in `SFT_Strategy.md` (read §0 first if you need
orientation, otherwise this runbook is self-contained).

If you are a continuing Claude session: every artifact this runbook
references is committed on branch `claude/intelligent-goldberg-4vywU`.
Pull it; everything is reproducible.

---

## 1. What we are doing

Four sequential LoRA training stages, one adapter continued across
all four. Each stage trains the same Qwen2.5-7B-Instruct base + that
adapter on a different subset of Phase 1 data.

```
base Qwen
  → phase1_lit       literacy across both substrate alphabets
  → phase1_same      same-dimensions rule application
  → phase1_diff      diff-dimensions rule application
  → phase1_mixed     cross-format application (final Phase 1)
```

After Phase 1 completes, Phase 2 (code generation) and Phase 3 (code
repair) continue the same LoRA. That's "Path α." Out of scope for
this runbook.

---

## 2. Prerequisites

**Environment:**
- A GPU machine with `axolotl` installed and working (Run 1 used
  RunPod with A100; same setup recommended).
- Python with `transformers`, `peft`, `torch` for the probe harness.
- This repo cloned, branch `claude/intelligent-goldberg-4vywU`.

**Disk:**
- ~25MB for the train datasets (committed in `Fine Tune Run 2/data_sft/`).
- ~100MB per LoRA adapter checkpoint × 4 stages = ~400MB minimum;
  more if you keep multiple checkpoints per stage (configs set
  `save_total_limit: 5`).
- ~15GB extra if Path β (merge between phases) is ever invoked.

**Things you do NOT need:**
- A separate `dev.jsonl` — Axolotl uses `val_set_size: 0.02` (train carve).
- A merge step between Phase 1 sub-stages — same LoRA continues.
- The 30 a2e_dev_hard or 34 a2e_final_hard puzzles — those are sacred
  for Phase 2/3 and end-of-run respectively. Phase 1 doesn't touch them.

---

## 3. Order of operations

Run each stage in sequence. Between stages, **probe → decide → proceed**.

### 3.1 Stage 0 — LIT (literacy)

```bash
# Train
axolotl train "Fine Tune Run 2/phase1_lit_axolotl.yaml"
# → outputs/phase1_lit/  (LoRA adapter)

# Probe
python3 "Fine Tune Run 2/run_probe.py" \
  --adapter outputs/phase1_lit \
  --probe   "Fine Tune Run 2/data_sft/phase1_lit_probe.jsonl"
# → phase1_lit_probe_report.json
# → phase1_lit_probe_failures.jsonl  (if any)
```

**Expected:** ~23,592 train records, ~256 probe records. Training
should converge fast — Run 1 hit val_loss < 0.01 in one epoch.

**Pass criteria (from the probe report):**

| Metric | Threshold |
|---|---|
| `pair_to_substrate` exact (same-dim) | ≥ 95% |
| `pair_to_substrate` exact (diff-dim) | ≥ 90% |
| `substrate_to_output` exact (same-dim) | ≥ 95% |

If a metric is below threshold: **extend LIT** (re-run with more
epochs or higher max_per_puzzle). Catching alphabet confusion here
is cheap; carrying it into SAME/DIFF/MIXED is expensive.

If all metrics pass: proceed to 3.2.

### 3.2 Stage 1 — SAME (same-dim rule application)

```bash
axolotl train "Fine Tune Run 2/phase1_same_axolotl.yaml"
# → outputs/phase1_same/  (continues outputs/phase1_lit)

python3 "Fine Tune Run 2/run_probe.py" \
  --adapter outputs/phase1_same \
  --probe   "Fine Tune Run 2/data_sft/phase1_same_probe.jsonl"
```

**Expected:** ~16,365 train records, ~302 probe records.

**Pass criteria:**

| Metric | Threshold |
|---|---|
| `pair_to_substrate` exact (same-dim) | ≥ 95% |
| `substrate_to_output` exact | ≥ 95% |
| `multi_pair_to_rule` exact (same-dim) | ≥ 90% |
| `test_substrate_prediction` exact (same-dim) | meaningfully above baseline |

**Also run the LIT probe** against the SAME adapter to check
forgetting:

```bash
python3 "Fine Tune Run 2/run_probe.py" \
  --adapter outputs/phase1_same \
  --probe   "Fine Tune Run 2/data_sft/phase1_lit_probe.jsonl"
```

LIT metrics should stay within 5 percentage points of their post-LIT
baseline. If they degrade more than that, you have a forgetting
problem — see §5.

### 3.3 Stage 2 — DIFF (diff-dim rule application)

```bash
axolotl train "Fine Tune Run 2/phase1_diff_axolotl.yaml"
python3 "Fine Tune Run 2/run_probe.py" \
  --adapter outputs/phase1_diff \
  --probe   "Fine Tune Run 2/data_sft/phase1_diff_probe.jsonl"
```

**Expected:** ~7,394 train records, ~105 probe records.

**Pass criteria:**

| Metric | Threshold |
|---|---|
| `pair_to_substrate` exact (diff-dim) | ≥ 90% |
| `multi_pair_to_rule` exact (diff-dim) | ≥ 85% |
| `test_substrate_prediction` exact (diff-dim) | meaningfully above baseline |

**Run forgetting checks** on the SAME probe (and LIT if you want
belt-and-suspenders):

```bash
python3 "Fine Tune Run 2/run_probe.py" \
  --adapter outputs/phase1_diff \
  --probe   "Fine Tune Run 2/data_sft/phase1_same_probe.jsonl"
```

Same-dim metrics must stay within 5pp of post-SAME baseline.

### 3.4 Stage 3 — MIXED (final Phase 1)

```bash
axolotl train "Fine Tune Run 2/phase1_mixed_axolotl.yaml"
python3 "Fine Tune Run 2/run_probe.py" \
  --adapter outputs/phase1_mixed \
  --probe   "Fine Tune Run 2/data_sft/phase1_mixed_probe.jsonl"
```

**Expected:** ~23,593 train records, ~407 probe records.

**Pass criteria:**

- All same-dim metrics within 5pp of post-SAME (no forgetting)
- All diff-dim metrics within 5pp of post-DIFF (no forgetting)
- `test_substrate_prediction` and `direct_output_grid` combined
  accuracy exceeds either single-stage baseline

Run all three prior probes against the MIXED adapter to confirm no
degradation.

If MIXED passes: **Phase 1 is done.** `outputs/phase1_mixed/` is the
final Phase 1 LoRA.

---

## 4. Verification

At any point you can re-verify the byte-level invariants of the
training data:

```bash
python3 "Fine Tune Run 2/verify_records.py"
```

Expected output: all 72,014 records across the 4 stages' train+probe
files pass invariants S1–S3, U1–U3, A1–A2, P1–P3.

If `verify_records.py` fails:
- Check `EXPECTED_SAME` / `EXPECTED_DIFF` / `EXPECTED_LIT` /
  `EXPECTED_MIXED` constants in `verify_records.py` against the
  `SYSTEM_MESSAGE_*` constants in `build_phase1_dataset.py`. They
  must match byte-for-byte.
- If a stage's records and its expected system message have drifted,
  regenerate that stage (`python3 "Fine Tune Run 2/build_phase1_dataset.py" --stage <stage>`).

---

## 5. Common issues

### 5.1 Probe fails its threshold

Don't panic. Options in increasing severity:

1. **Train one more epoch on the same stage.** Bump `num_epochs` in
   the stage's axolotl yaml from 1 to 2. Re-train. Re-probe.
2. **Increase max_per_puzzle in the generator** (default 24 → 48).
   Regenerate that stage's dataset:
   ```bash
   python3 "Fine Tune Run 2/build_phase1_dataset.py" \
     --stage <lit|same|diff|mixed> --max-per-puzzle 48
   ```
   Re-train. Re-probe.
3. **Tighter LR.** Halve `learning_rate` in the stage's yaml
   (1.2e-4 → 6e-5), train another short run, probe.

### 5.2 Forgetting between stages

Symptom: SAME probe degrades >5pp after DIFF training. Or similar.

Options:

1. **Increase carry weight** in the next stage's mix. DIFF currently
   carries 5% pair_to_substrate; raise to 10% in `build_phase1_dataset.py`
   `STAGE_CONFIG["diff"]["task_mix"]`. Regenerate, retrain.
2. **Lower LR for the offending stage.** Halve `learning_rate` in
   that stage's axolotl yaml. Retrain.
3. **Switch to Path β** (merge between phases). See `SFT_Strategy.md`
   §9.3. Not needed unless Path α is clearly broken.

### 5.3 Out of memory / OOM during training

Run 1's config used `micro_batch_size: 2, gradient_accumulation_steps: 16`
on A100. If you OOM:

1. Lower `micro_batch_size` to 1 and raise `gradient_accumulation_steps`
   to 32 (preserves effective batch).
2. Lower `sequence_len` from 8192 to 4096 — check token-length stats
   first to make sure your records fit:
   ```python
   python3 -c "
   import json, gzip
   for p in ['phase1_lit', 'phase1_same', 'phase1_diff', 'phase1_mixed']:
       lengths = []
       with gzip.open(f'Fine Tune Run 2/data_sft/{p}_train.jsonl.gz', 'rt') as f:
           for line in f:
               r = json.loads(line)
               total = sum(len(m['content']) // 3 + 1 for m in r['messages'])
               lengths.append(total)
       lengths.sort()
       print(f'{p}: max={lengths[-1]}, p99={lengths[int(len(lengths)*0.99)]}')
   "
   ```
3. Enable QLoRA (`load_in_4bit: true`). Run 1 didn't need this but
   it's an option.

### 5.4 Train file not found by Axolotl

Axolotl reads `.jsonl.gz` directly. If it complains about the file:
- Make sure the path in the yaml is exactly:
  `Fine Tune Run 2/data_sft/phase1_<stage>_train.jsonl.gz`
- Run from the repo root (not from inside `Fine Tune Run 2/`).
- The folder name "Fine Tune Run 2" has spaces; if your shell needs
  it escaped, that's your shell's problem, not Axolotl's.

### 5.5 Probe harness errors

`run_probe.py` requires `transformers`, `peft`, `torch`, and the
Qwen2.5-7B-Instruct base model accessible (it'll download from HF on
first run, ~15GB). If it can't find your adapter dir or probe file,
check the paths. The script supports `--limit N` for debugging on a
small subset.

---

## 6. File map

```
Fine Tune Run 2/
  # Strategy
  SFT_Strategy.md                       full strategy doc (philosophy)
  RUNBOOK.md                            this file (operational)

  # Trainer configs (one per stage)
  phase1_lit_axolotl.yaml               from base Qwen
  phase1_same_axolotl.yaml              continues phase1_lit
  phase1_diff_axolotl.yaml              continues phase1_same
  phase1_mixed_axolotl.yaml             continues phase1_diff

  # Scripts
  build_phase1_dataset.py               dataset generator
  build_splits.py                       initial split + isolate frozen 34
  verify_records.py                     byte-level invariant checker
  verify_augmentations.py               rule-preservation checks
  run_probe.py                          per-format exact-match harness
  classify_origin.py                    A1/A2 origin classifier

  # Datasets (committed, regenerable)
  data_sft/
    phase1_lit_train.jsonl.gz           23,592 records
    phase1_lit_probe.jsonl              256 records
    phase1_lit_manifest.json
    phase1_same_train.jsonl.gz          16,365 records
    phase1_same_probe.jsonl             302 records
    phase1_same_manifest.json
    phase1_diff_train.jsonl.gz          7,394 records
    phase1_diff_probe.jsonl             105 records
    phase1_diff_manifest.json
    phase1_mixed_train.jsonl.gz         23,593 records
    phase1_mixed_probe.jsonl            407 records
    phase1_mixed_manifest.json

  # Splits (puzzle ids, locked)
  splits/
    phase1_splits.json                  full splits manifest
    frozen_final_eval_ids.txt           34 ids — sacred end-of-run
    phase1_probe_ids.txt                50 ids — between-stage probe
    api_eval_ids.txt                    50 ids — API testing across phases

  # Puzzles (the source corpus)
  puzzles/                              1886 .json files (~1100 content-unique)
  puzzles_frozen/                       34 .json files — DO NOT READ during training
```

Top-level (shared with Run 1):
```
substrate.py                            substrate library
scripts/test_diffsize_substrate.py      substrate regression test
```

---

## 7. Reading the probe report

`run_probe.py` writes `<probe_stem>_probe_report.json` next to the
probe file. Structure:

```json
{
  "adapter": "outputs/phase1_lit",
  "probe":   "Fine Tune Run 2/data_sft/phase1_lit_probe.jsonl",
  "n_records": 256,
  "by_key": {
    "pair_to_substrate|same_size":   {"n": 102, "correct": 98, "exact_match": 0.961, "threshold": 0.95, "passed": true},
    "pair_to_substrate|diff_size":   {"n": 52, "correct": 48, "exact_match": 0.923, "threshold": 0.90, "passed": true},
    "substrate_to_output|same_size": {"n": 102, "correct": 100, "exact_match": 0.980, "threshold": 0.95, "passed": true}
  },
  "summary": {
    "overall_exact_match": 0.961,
    "overall_n": 256,
    "overall_correct": 246
  }
}
```

`<probe_stem>_probe_failures.jsonl` contains one record per wrong
prediction with provenance + expected + got. Useful for diagnosing
*what* the model is getting wrong, not just *how much*.

The harness also prints a human-readable table. Use the JSON for
automation; use the table for eyeballing.

---

## 8. Held-out discipline

Read this if you're tempted to touch anything other than the listed
files during Phase 1.

| Set | When you can touch it during Phase 1 |
|---|---|
| `phase1_<stage>_train.jsonl.gz` | Yes — Axolotl reads this as the training input |
| `phase1_<stage>_probe.jsonl` | Yes — only via `run_probe.py` between stages |
| `puzzles/` | Yes — by the generator only |
| Axolotl train-carve (`val_set_size: 0.02`) | Yes — Axolotl reads it automatically for loss monitoring |
| `api_eval_ids.txt` (50 puzzle ids) | OK for API runs — never gradient |
| `a2e_dev_hard` (30 puzzles, identified in `splits/phase1_splits.json`) | **NO during Phase 1.** Phase 2/3 only. |
| `a2e_final_hard` (34 puzzles, locked in `puzzles_frozen/`) | **NO until end of Phase 3.** |

If a script accidentally reads a forbidden file, treat it as a bug.
The generator is designed to literally not see `puzzles_frozen/`
(different directory) and to exclude probe/api_eval ids by id list.

---

## 9. What happens next (after Phase 1)

Out of scope for this runbook, but for orientation:

1. **Phase 2 (Code Solver):** continues `outputs/phase1_mixed/` LoRA,
   trains on `def solve(input_grid)` Python targets. Different system
   message (`Code Solver`). Configs and data not yet generated.
2. **Phase 3 (Code Repair):** continues Phase 2 LoRA, trains on
   validator-feedback → corrected-code. Different system message
   (`Code Repair`).
3. **End-of-run eval:** run the final adapter against the 34 sacred
   puzzles in `puzzles_frozen/`. That's the headline number.

Phase 2/3 design lessons from Run 1 (shape blind spot, missing
imports, hardcoded values, etc.) are documented in `SFT_Strategy.md`
§10.

---

## 10. If something is unclear or broken

Read `SFT_Strategy.md`. The strategy doc has the *why* behind every
choice this runbook says to make. Sections most likely to help:

- §0 — orientation (core thesis + failure taxonomy)
- §2 — splits & hold-out discipline
- §4 — Phase 1 four-stage curriculum (this runbook is its operational form)
- §9 — execution chain (Path α = default)
- §10 — Run 1 lessons for Phase 2/3

If the issue is a script bug rather than a strategy question, the
relevant scripts are all <500 lines and stdlib-only (except `run_probe.py`
which needs transformers/peft/torch). Read them.
