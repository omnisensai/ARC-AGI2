# Phase 1 Runbook — Training Pipeline Execution

Operational handoff for executing Run 2 Phase 1. Procedural only —
strategy lives in `SFT_Strategy.md` (read §0 first if you need
orientation, otherwise this runbook is self-contained).

If you are a continuing Claude session: every artifact this runbook
references is committed on branch `claude/intelligent-goldberg-4vywU`.
Pull it; everything is reproducible.

---

## 1. What we are doing

Five sequential LoRA training stages, one adapter continued across
all five. Each stage trains the same Qwen2.5-7B-Instruct base + that
adapter on a different subset of Phase 1 data. The two T alphabets
(pixel for same-size pairs, facts for diff-size pairs) are taught in
isolation and reunite only in the final `mixed` stage.

```
base Qwen
  → phase1_same_lit    same-size single-pair literacy (pixel T)
  → phase1_diff_lit    diff-size single-pair literacy (facts T)
  → phase1_same_rule   same-size multi-pair rule application
  → phase1_diff_rule   diff-size multi-pair rule application
  → phase1_mixed       both alphabets, all formats (final Phase 1)
```

System prompts are defined once in `phase1_prompts.py` (single source of
truth, mirrored in `PROMPTS.md`). Do not retype them.

After Phase 1 completes, Phase 2 (code generation) and Phase 3 (code
repair) continue the same LoRA. That's "Path α." Out of scope for
this runbook.

---

## 2. Prerequisites

**Environment:**
- A GPU machine with `axolotl`. **Bare PyTorch RunPod images do NOT have
  axolotl or flash-attn preinstalled** — either pick an axolotl template
  image, or install on a bare pod (see P-INSTALL below). A100-80GB is
  the tested GPU.
- Python with `transformers`, `peft`, `torch` for the probe harness.
- This repo cloned, branch `claude/gifted-mayer-3ITc1`.

**Disk:**
- ~25MB for the train datasets (committed in `Fine Tune Run 2/data_sft/`).
- ~100MB per LoRA adapter checkpoint × 5 stages = ~500MB minimum;
  more if you keep multiple checkpoints per stage (configs set
  `save_total_limit: 5`).
- ~15GB extra if Path β (merge between phases) is ever invoked.

**Things you do NOT need:**
- A separate `dev.jsonl` — Axolotl uses `val_set_size: 0.02` (train carve).
- A merge step between Phase 1 sub-stages — same LoRA continues.
- The 30 a2e_dev_hard or 34 a2e_final_hard puzzles — those are sacred
  for Phase 2/3 and end-of-run respectively. Phase 1 doesn't touch them.

---

## 2.5 Startup pitfalls — the first-100-iterations tax (READ FIRST)

Every fresh pod loses an hour to the same handful of cache / memory /
auth errors. Do these *before* your first `axolotl train` and most of
them never happen. (Harvested from `scripts/preflight.sh` and
`docs/runbook_vllm_eval.md`.)

### P0. Redirect ALL caches off the tiny overlay disk, BEFORE any download

RunPod `/` is a ~20 GB overlay; `/workspace` is the big network volume.
Qwen-7B is ~15 GB and HF caches to `~/.cache` (= overlay) by default →
`OSError: Disk quota exceeded` mid-download. Set, persist, and source:

```bash
export HF_HOME=/workspace/hf_cache/huggingface
export HUGGINGFACE_HUB_CACHE=/workspace/hf_cache/huggingface/hub
export TRANSFORMERS_CACHE=/workspace/hf_cache/huggingface/hub
export TMPDIR=/workspace/tmp
export HF_HUB_DISABLE_XET=1      # Xet keeps a SECOND copy of weights — disable
export PYTHONUNBUFFERED=1        # so logs aren't silently buffered
mkdir -p /workspace/hf_cache/huggingface/hub /workspace/tmp
echo 'source /root/.env_train' >> ~/.bashrc   # after writing the above into it
```

### P1. axolotl's tokenized cache is stale-prone (the silent footgun)

axolotl tokenizes once and caches to `dataset_prepared_path`. If you
regenerate data or edit a config, it **reuses the old cache and trains
on stale data without warning.** Whenever you change a stage's data or
yaml, nuke that stage's prepared dir first:

```bash
rm -rf "Fine Tune Run 2/data_sft/prepared/phase1_<stage>"
```

Also make sure `outputs/` lives on `/workspace`, not the overlay disk.

### P2. Dry-run the config before burning GPU hours

```bash
axolotl preprocess "Fine Tune Run 2/phase1_same_lit_axolotl.yaml"
```

This tokenizes without training — surfaces config / schema / chat-template
errors in ~1 min instead of after a 2-minute model load. Run it once per
stage config the first time.

### P3. Confirm the chat template matches training (one-time)

Training uses axolotl's built-in `chat_template: qwen2`. The eval/probe
path uses the tokenizer's template (pinned in
`Fine Tune Run 2/tokenizer_config.json`). They should be identical
ChatML, but verify once on the box:

```bash
python3 -c "
from transformers import AutoTokenizer
t = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct')
print(t.chat_template[:120])"
```

### P4. flash-attention must actually be installed

Configs set `flash_attention: true`. If flash-attn isn't built for your
torch/CUDA, training dies at model load. Either
`pip install flash-attn --no-build-isolation`, or set
`flash_attention: false` in the yaml.

### P5. Run from the repo root; the folder name has a space

All dataset paths are `Fine Tune Run 2/...` relative to the repo root.
Run axolotl from the repo root and quote the path (the space breaks
unquoted shells).

### P6. Auth — both bite on a fresh pod

- **GitHub clone (private repo) — the `403` that wastes everyone's
  morning.** A plain `git clone https://github.com/...` of the PRIVATE
  repo with no credentials returns `error: 403` and does NOT prompt —
  so the clone fails, then every `cd ARC-AGI2` / `git ...` after it
  errors with "not a git repository". The fix is to **seed the
  credential BEFORE cloning** (do not toggle the repo public/private):

  ```bash
  # one-time per fresh pod (PAT = fine-grained, omnisensai/ARC-AGI2,
  # Contents: Read and write)
  git config --global credential.helper 'store --file=/workspace/.git-credentials'
  read -rsp 'paste GitHub PAT: ' TOKEN; echo
  echo "https://omnisensai:${TOKEN}@github.com" > /workspace/.git-credentials
  chmod 600 /workspace/.git-credentials
  unset TOKEN
  # now the clone uses the stored credential — no prompt, no 403
  cd /workspace && git clone https://github.com/omnisensai/ARC-AGI2.git
  ```

  The credential file lives on `/workspace`, so it survives Stop/restart
  — you only redo this after a full Terminate.

- **Hugging Face:** `hf auth login`. Base Qwen is public; the adapter
  backup repo is private (needs Contents: Read+Write). The CLI is now
  `hf`, not `huggingface-cli`.

### P-INSTALL. Bare image has no axolotl / flash-attn (install, or use a template)

A fresh RunPod PyTorch image typically has `torch` but **not** `axolotl`
or `flash_attn`. Symptom from the block-3 sanity check: `axolotl MISSING`,
`No module named 'flash_attn'`. Two ways:

- **Best: launch the pod from an axolotl template image** (axolotl +
  flash-attn + matched torch preinstalled) — skips all of the below.
- **On a bare pod, install (order matters — `hf` ships INSIDE
  huggingface_hub, which axolotl pulls in, so install axolotl FIRST):**
  ```bash
  pip install --no-cache-dir axolotl 2>&1 | tail -15
  axolotl --help >/dev/null 2>&1 && echo OK || echo FAILED
  hf auth login                              # paste HF token (hf exists now)
  pip install flash-attn --no-build-isolation 2>&1 | tail -5   # optional
  ```
  If flash-attn is slow to compile or fails, **don't fight it** — set
  `flash_attention: false` in each `phase1_*_axolotl.yaml` (or
  `sed -i 's/flash_attention: true/flash_attention: false/'`). On an
  80 GB A100 with these batch/seq settings, training fits without it.

  **Known cascade: `pip install axolotl` bumps torch (2.4→2.8) and
  orphans torchvision/torchaudio**, which then crash on import with
  `RuntimeError: operator torchvision::nms does not exist`, cascading
  into `Could not import module 'PreTrainedModel'` and `axolotl --help`
  failing. LLM LoRA training needs neither, so just remove them:
  ```bash
  pip uninstall -y torchvision torchaudio
  axolotl --help >/dev/null 2>&1 && echo OK || echo FAILED
  ```

### P7. Setup in a Jupyter Terminal, not notebook cells

`File → New → Terminal`. Heredocs and multi-line blocks mangle in
`%%bash`/`!` cells. And never paste a Python script into a bash prompt
(symptom: a wall of `command not found` for `import`, `Counter`, etc.).

### Symptom → cause (training)

| Symptom | Cause / fix |
|---|---|
| `OSError: Disk quota exceeded` during download | cache on overlay disk / Xet — do P0 before anything |
| Trained, but results look like an old config | stale `dataset_prepared_path` — P1, delete the prepared dir |
| `axolotl --help` fails: `torchvision::nms does not exist` / `Could not import PreTrainedModel` | torch got bumped, torchvision orphaned — `pip uninstall -y torchvision torchaudio` (P-INSTALL) |
| Error at model load mentioning flash-attn | P4 — install flash-attn or set `flash_attention: false` |
| CUDA OOM | §5.3 — micro_batch 1 + grad_accum 32, or seq_len 4096, or 4bit |
| `FileNotFoundError` on the `.jsonl.gz` | wrong cwd or unquoted space — run from repo root, quote the path (P5) |
| `git clone` → `error: 403` then a cascade of "not a git repository" | private repo, no credential — seed `/workspace/.git-credentials` BEFORE cloning (P6). Do NOT toggle repo visibility. |
| `404` on a private HF/GitHub repo | token lacks scope for that exact repo (P6) |
| empty/garbled multi-line paste | notebook cell instead of terminal (P7) |

---

## 3. Order of operations

Run each stage in sequence. Between stages, **probe → decide → proceed**.
General pattern per stage:

```bash
axolotl train "Fine Tune Run 2/phase1_<stage>_axolotl.yaml"
python3 "Fine Tune Run 2/run_probe.py" \
  --adapter outputs/phase1_<stage> \
  --probe   "Fine Tune Run 2/data_sft/phase1_<stage>_probe.jsonl"
```

Each `_axolotl.yaml` already sets `lora_model_dir` to the previous
stage's output, so the adapter continues automatically.

### 3.1 same_lit — same-size literacy (from base Qwen)

```bash
axolotl train "Fine Tune Run 2/phase1_same_lit_axolotl.yaml"
python3 "Fine Tune Run 2/run_probe.py" \
  --adapter outputs/phase1_same_lit \
  --probe   "Fine Tune Run 2/data_sft/phase1_same_lit_probe.jsonl"
```

**Expected:** ~16,294 train records, ~204 probe records.

**Pass criteria:**

| Metric | Threshold |
|---|---|
| `pair_to_substrate` exact (same-size) | ≥ 95% |
| `substrate_to_output` exact (same-size) | ≥ 95% |

If below threshold, extend this stage (more epochs / higher
`--max-per-puzzle`) before moving on.

### 3.2 diff_lit — diff-size literacy (continues same_lit)

```bash
axolotl train "Fine Tune Run 2/phase1_diff_lit_axolotl.yaml"
python3 "Fine Tune Run 2/run_probe.py" \
  --adapter outputs/phase1_diff_lit \
  --probe   "Fine Tune Run 2/data_sft/phase1_diff_lit_probe.jsonl"
```

**Expected:** ~7,394 train records, ~52 probe records.

**Pass criteria:** `pair_to_substrate` exact (diff-size) ≥ 90%.

**Forgetting check** — re-run the same_lit probe against this adapter;
same-size metrics should stay within 5pp of their post-same_lit
baseline.

### 3.3 same_rule — same-size rule application (continues diff_lit)

```bash
axolotl train "Fine Tune Run 2/phase1_same_rule_axolotl.yaml"
python3 "Fine Tune Run 2/run_probe.py" \
  --adapter outputs/phase1_same_rule \
  --probe   "Fine Tune Run 2/data_sft/phase1_same_rule_probe.jsonl"
```

**Expected:** ~16,364 train records, ~302 probe records.

**Pass criteria:**

| Metric | Threshold |
|---|---|
| `multi_pair_to_rule` exact (same-size) | ≥ 90% |
| `test_substrate_prediction` exact (same-size) | meaningfully above baseline |
| `pair_to_substrate` / `substrate_to_output` (carry) | ≥ post-literacy baseline |

### 3.4 diff_rule — diff-size rule application (continues same_rule)

```bash
axolotl train "Fine Tune Run 2/phase1_diff_rule_axolotl.yaml"
python3 "Fine Tune Run 2/run_probe.py" \
  --adapter outputs/phase1_diff_rule \
  --probe   "Fine Tune Run 2/data_sft/phase1_diff_rule_probe.jsonl"
```

**Expected:** ~7,394 train records, ~105 probe records.

**Pass criteria:**

| Metric | Threshold |
|---|---|
| `multi_pair_to_rule` exact (diff-size) | ≥ 85% |
| `test_substrate_prediction` exact (diff-size) | meaningfully above baseline |

**Forgetting check** — re-run the same_rule probe; same-size metrics
within 5pp of post-same_rule baseline.

### 3.5 mixed — both alphabets, all formats (final Phase 1)

```bash
axolotl train "Fine Tune Run 2/phase1_mixed_axolotl.yaml"
python3 "Fine Tune Run 2/run_probe.py" \
  --adapter outputs/phase1_mixed \
  --probe   "Fine Tune Run 2/data_sft/phase1_mixed_probe.jsonl"
```

**Expected:** ~23,593 train records, ~407 probe records.

**Pass criteria:**

- All same-size metrics within 5pp of post-same_rule (no forgetting)
- All diff-size metrics within 5pp of post-diff_rule (no forgetting)
- `test_substrate_prediction` + `direct_output_grid` combined accuracy
  exceeds either single-stage baseline

Run all prior-stage probes against the mixed adapter to confirm no
degradation. If mixed passes: **Phase 1 is done.**
`outputs/phase1_mixed/` is the final Phase 1 LoRA.

---

## 4. Verification

At any point you can re-verify the byte-level invariants of the
training data:

```bash
python3 "Fine Tune Run 2/verify_records.py"
```

Expected output: it first confirms `phase1_prompts.py` matches
`PROMPTS.md`, then checks all 72,109 records across the 5 stages'
train+probe files against invariants S1–S3, U1–U3, A1–A2, P1–P3.

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
     --stage <same_lit|diff_lit|same_rule|diff_rule|mixed> --max-per-puzzle 48
   ```
   Re-train. Re-probe.
3. **Tighter LR.** Halve `learning_rate` in the stage's yaml
   (1.2e-4 → 6e-5), train another short run, probe.

### 5.2 Forgetting between stages

Symptom: same_rule probe degrades >5pp after diff_rule training. Or similar.

Options:

1. **Increase carry weight** in the next stage's mix. The rule stages
   carry a small literacy slice; raise it in `build_phase1_dataset.py`
   `STAGE_CONFIG[<stage>]["task_mix"]`. Regenerate, retrain.
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
   for p in ['phase1_same_lit', 'phase1_diff_lit', 'phase1_same_rule', 'phase1_diff_rule', 'phase1_mixed']:
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

  # Prompts (single source of truth)
  phase1_prompts.py                     5 stage prompts; self-checks PROMPTS.md
  PROMPTS.md                            human-readable prompt spec

  # Trainer configs (one per stage)
  phase1_same_lit_axolotl.yaml          from base Qwen
  phase1_diff_lit_axolotl.yaml          continues phase1_same_lit
  phase1_same_rule_axolotl.yaml         continues phase1_diff_lit
  phase1_diff_rule_axolotl.yaml         continues phase1_same_rule
  phase1_mixed_axolotl.yaml             continues phase1_diff_rule

  # Scripts
  build_phase1_dataset.py               dataset generator (imports phase1_prompts)
  build_splits.py                       initial split + isolate frozen 34
  verify_records.py                     byte-level invariant checker
  verify_augmentations.py               rule-preservation checks
  run_probe.py                          per-format exact-match harness
  classify_origin.py                    A1/A2 origin classifier

  # Datasets (committed, regenerable)
  data_sft/
    phase1_same_lit_train.jsonl.gz      16,294 records
    phase1_same_lit_probe.jsonl         204 records
    phase1_same_lit_manifest.json
    phase1_diff_lit_train.jsonl.gz      7,394 records
    phase1_diff_lit_probe.jsonl         52 records
    phase1_diff_lit_manifest.json
    phase1_same_rule_train.jsonl.gz     16,364 records
    phase1_same_rule_probe.jsonl        302 records
    phase1_same_rule_manifest.json
    phase1_diff_rule_train.jsonl.gz     7,394 records
    phase1_diff_rule_probe.jsonl        105 records
    phase1_diff_rule_manifest.json
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
