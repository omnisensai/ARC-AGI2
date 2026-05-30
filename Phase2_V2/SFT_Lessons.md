# SFT Lessons — ARC-AGI Substrate-Curriculum Fine-Tuning

Lessons learned from V1 (Run 2, scored 24% on held-out) and V2 (Run 1, this round).
Written 2026-05-30 after a full night of debugging V2 underperformance and
re-establishing what we actually know.

---

## 1. Training Lessons

### 1.1 The methodology works — we have hard evidence

Measured solve rates on 20 same-size ARC puzzles, sampled greedy/T=0.5, identical prompt:

| Setup | Solve Rate | Note |
|---|---|---|
| Qwen2.5-7B-Instruct (base) | **0/20** | Behavioral collapse — loops, hallucinated dialog, token degeneration |
| Qwen2.5-Coder-7B-Instruct | **0/20** | Fluent Python, always wrong rule, hardcoded color tables |
| V1 LoRA (substrate-curriculum + code, full chain) | **24%** on held-out | Original Run 2 measurement |

**Implication**: any positive solve rate is a methodology contribution, not noise.
Code training alone does not give visual rule extraction. Instruction tuning alone
does not either. The substrate-curriculum is the only path off the 0% floor we have
evidence for.

### 1.2 Start from Qwen2.5-Coder-7B-Instruct, NOT base Qwen2.5-7B-Instruct

On the same 20 puzzles, Coder produced **one clean self-contained solver in 20/20 cases**.
Base Qwen produced one clean solver in **~5/20 cases**. The other 15+ ranged from:

- Multi-solver "let me try again" loops (8 puzzles)
- Token-degeneration meltdown (`0000…`, `4444…`, `for i in '333'…` repeated 150x)
- Hallucinated multi-turn dialog (`user\n…\nCertainly! Let's analyze…`)
- Leaked shell prompts (`root@e3241538a7a6:/workspace/ARC-AGI2#`)
- Gross syntax errors (`def def`, `range(range(len(rows)))`)

**Coder's value is OUTPUT DISCIPLINE, not ARC ability.** Both get 0% — but Coder gets
to 0% while always emitting a clean parseable solver. Starting from Coder gives that
discipline for free; you only need to train rule-extraction. Starting from base Qwen
forces you to teach output discipline AND rule extraction simultaneously, doubling
the training burden.

### 1.3 Don't skip Phase 1 substrate literacy

V1's chain was:
```
phase1_same_lit → phase1_diff_lit → phase1_same_rule → phase1_diff_rule → phase1_mixed → phase2_code
```
Each stage continued the previous LoRA. The model learned to *recognize* transformations
(T-maps, regions, markers) on simpler tasks before being asked to *write code* that
implements them. **Result: 24% on held-out, 85% in-distribution.**

V2's chain was:
```
base Qwen → phase2_code
```
Single SFT stage straight from base. **Result: trains to <0.001 eval loss but
collapses at inference — Chinese leak, repetition collapse, hallucinated puzzle
IDs, fails most held-out.**

The lesson: substrate literacy is load-bearing. The model needs to see "this is a
rectangle / marker column / enclosed region" thousands of times before it can write
`def infer_T` that does the right thing. Skipping it is the V2 mistake; do not repeat.

### 1.4 Prompt format is load-bearing — pin it and never change it

Discovered the hard way: V1 was trained on a totally different SYSTEM and USER
format than V2. When we tried to evaluate V1 with V2's prompt (`T encodes...` + ask
for `infer_T`), V1 produced garbled corrupted Python (`inrange` instead of `in range`,
missing brackets, repetition collapse). With V1's own prompt (`Code Solver.\n...` +
ask for monolithic `def solve`), V1 produces coherent code.

**The LoRA is brittle to out-of-distribution prompts in a way the base model isn't.**
Fine-tuning sharpens the model AROUND a specific prompt distribution; deviation
produces gibberish, not graceful degradation.

Rules:
1. Bundle SYSTEM and prompt-building helpers (`render_pairs`, `build_user_prompt`)
   in a single Python module imported at BOTH training and eval time. Never copy-paste.
2. Save the exact `apply_chat_template` chain used in training. Reuse byte-for-byte
   at inference.
3. Save the tokenizer ALONGSIDE the adapter. Pin its version. If you reload it later
   with a newer transformers and it errors, that's a sign you've drifted — investigate,
   don't paper over.

### 1.5 Hyperparameters: V1's recipe beat V2's

| Parameter | V1 (24% held-out) | V2 (current run) | Verdict |
|---|---|---|---|
| Base model | Qwen2.5-7B-Instruct | Qwen2.5-7B-Instruct | Use Coder next time (§1.2) |
| Chain | Phase 1 stages → code | Direct to code | Use chain (§1.3) |
| Learning rate | 0.00012 | 0.0002 | Lower wins |
| Weight decay | 0.01 | 0.0 | Keep some decay |
| Sequence length | 8192 | 4096 | Longer wins (more context per example) |
| LoRA rank | (V1 default) | 32 | Try 64+ for V2.1 |
| Sample packing | yes | yes | keep |
| `train_on_inputs` | false | false | keep (completion-only loss) |

V2 traded more aggressive LR + shorter sequences for faster training. The result was
faster fitting and worse generalization. The classic mistake.

### 1.6 Data hygiene — strip leaks aggressively before training

V2 trained on 740 canonical solver `.py` files. **192 of them had a docstring leak**:
```python
"""Canonical solver for ARC puzzle 00d62c1b"""
```
The model memorized these and now hallucinates puzzle IDs at inference time
(emitting `# Canonical solver for 4938a36c` when shown an unrelated puzzle).

Before training, run AST-grep / regex over EVERY training source file to detect:
1. Puzzle-ID strings (`[0-9a-f]{8}`) in any comment / docstring / variable name
2. Hardcoded grids that match any puzzle's input or output exactly
3. Trailing metadata blocks ("origin:", "puzzle_id:", "stage:")

Anything that hardcodes a puzzle identity in the training target is a leak. The
model will learn to look it up rather than learn the rule.

### 1.7 Inference characteristics — what to set, what to expect

**Temperature**: 0.5 with top_p=0.9 is the right default for trained LoRAs.
T=0 (greedy) is BRITTLE to backend/precision drift — if the most-likely token is
even slightly miscomputed, greedy locks in the error and emits corrupted Python.
T=0.5 has enough variance to escape stuck states without hallucinating wildly.

**Max new tokens**: 2048 is enough for our canonical solver style. Base Qwen will
ramble to whatever cap you set (each puzzle takes 120s at 4096 tokens). Fine-tuned
models emit EOS quickly — generation time per puzzle is a discipline signal in
itself. If your trained LoRA is running 50s+/puzzle, something's wrong (precision
drift, OOD prompt, or training didn't teach EOS discipline).

**Beam search**: `num_beams=4` recommended for the production eval. Catches
bad-token cascades that greedy can't recover from. ~3-4x slower but better
solve rate on borderline cases.

**Repetition penalty / no_repeat_ngram**: counterintuitive — these HURT code generation
because canonical solvers legitimately repeat (`def X(input_grid)`, `for r in range(rows)`).
Leave at defaults (1.0 and 0) unless you see specific n-gram loops.

### 1.8 Failure-mode taxonomy — how to read a model's wrong output

Classify failures into these buckets before drawing any conclusion:

| Bucket | Meaning | Signal |
|---|---|---|
| **PASS** | Solver runs, output matches expected | model has the rule |
| **WRONG_OUTPUT** | Solver runs, wrong output | model has a wrong rule (cognitive) |
| **SHAPE_MISMATCH** | Solver runs, wrong dimensions | output planning broken |
| **RUNTIME_ERROR** | Solver crashes | code-emission broken |
| **TIMEOUT** | Solver runs >3s | infinite loop / quadratic bug |
| **EMPTY_OR_INVALID** | No `def solve` or syntax error | discipline broken |
| **HARDCODED** | Solver passes only because it hardcoded the answer | leak or memorization |

Pay attention to the RATIO. A run with high WRONG_OUTPUT and low EMPTY_OR_INVALID
means the model is in the right frame but extracting wrong rules — a methodology
problem. A run with high EMPTY_OR_INVALID means output discipline broke — usually
an inference-environment issue. A run with high HARDCODED means you have a data leak.

---

## 2. Setup & Technical Lessons

### 2.1 Pin your environment, or it WILL break under you

The night ate hours on:
- vLLM 0.22 install bumped torch 2.8 → 2.11, broke flash-attn ABI compatibility
- The flash-attn break cascaded into cuDNN errors during plain `torch.matmul`
- Pinning `transformers<5.0` + `peft<0.16` to recover torch 2.4 compat
- V1's adapter tokenizer (saved with older transformers) failing to load under
  newer transformers (`extra_special_tokens` dict vs list)

**Treat the inference env as part of the artifact.** Whenever you save a LoRA
checkpoint, also save:
1. `pip freeze > requirements.txt`
2. The actual torch / transformers / peft / flash-attn / axolotl versions used
3. The CUDA + cuDNN versions
4. The tokenizer that produced the training tokens
5. The `attn_implementation` used in training

When you later try to reproduce the eval, recreate this exact env in a fresh
container before loading the adapter. **Without this, you cannot reproduce a
trained model.** We learned this when V1 stopped reproducing its 24% — it wasn't
that V1 broke, it's that the inference path we used didn't match the training path.

### 2.2 Attention implementation drift is real

Training: flash-attn (default in axolotl + Qwen recipe)
V1 eval: `attn_implementation="sdpa"`
V2 eval: `attn_implementation="eager"` (after vLLM broke cuDNN)

Each combination gives subtly different attention scores. Across 32 transformer
layers, these compound. In practice we observed:
- Greedy decoding with eager attention produced systematic typos (`inrange` instead
  of `in range`) that did not appear at training time
- Solve rate visibly differs between sdpa and eager on the same checkpoint

**Match the training-time attention implementation at inference.** If flash-attn
won't install on the eval pod, you have an environment problem, not an inference
problem — fix it.

### 2.3 Preflight discipline saves hours

Before kicking off a 100-puzzle eval that will take 30-90 minutes:

```bash
# 1. Smoke test: 1 puzzle, see real output
python3 eval_script.py --limit 1

# 2. Check the actual prompt being sent (paste it, look at it)
python3 -c "from build_micro_sft import SYSTEM, render_pairs; ..."

# 3. Verify failure-mode tally on first 5
python3 eval_script.py --limit 5
```

We burned 2 hours waiting on full 100-puzzle runs that were clearly failing within
the first 5. ETA from the run script is a much faster signal than waiting for
SOLVE RATE.

### 2.4 Save JSONL with per-line flush — partial runs preserve data

Both `run_bucket1_eval_hf.py` and `baseline_eval.py` write each puzzle's result
as one JSON line and call `fh.flush()` after each. This means:
- Ctrl+C at any point preserves all completed puzzles
- You can `head -n 20 results.jsonl` to slice the first N for comparison
- Crashes mid-run don't lose work

Critical for runs that take 30+ min. Always write JSONL per-line, never batch
writes to the end.

### 2.5 Puzzle data format pitfalls

Two parallel puzzle stores live in this repo:
- `Phase2_V2/Puzzle_Database/<pid>_<suffix>.json` — TEXT-encoded grids (newline strings)
  - Some `_A2T.json` files are CORRUPTED to 90x1 column-vector format. Use `_A2E.json` for eval.
- `Phase2_V2/canonical/ground_truth_puzzles/<pid>.json` — JSON-array format (list of list of int)
  - Verified clean. This is the format the V2 training pipeline used.

**Always load training-time puzzles from the same source training used.**
V2 training used `canonical/ground_truth_puzzles/`, so V2 eval must too. V1's
`run_phase2_eval.py` expects the text-encoded `Puzzle_Database/` format — using the
wrong dir gives a confusing `.strip() on list` error.

When loading puzzle data, write a defensive loader that:
1. Tries multiple known paths in priority order
2. Detects the format (text vs list) and parses accordingly
3. Sanity-checks the resulting grid shape against expected dimensions
4. Errors loudly if a puzzle is found in the wrong format

### 2.6 Git auth on ephemeral pods is a recurring pain — fix it once

Three workarounds we used this session:
1. **Temporarily make repo public** → `git push` → make private again. Fast but error-prone.
2. **Personal Access Token** with `repo` scope → set as password → cache with
   `git config credential.helper 'cache --timeout=86400'`. One-time setup, 24h silence.
3. **Push files via GitHub MCP tool** in the AI session — bypasses git entirely.

Option 2 is the right long-term answer. Generate a 90-day PAT once, paste it
once, then never deal with the prompt again. Pin the username/email at session start:
```bash
git config user.email "elinnguy3n@gmail.com"
git config user.name "Omnisensai"
```

### 2.7 RunPod / ephemeral container reality

- Container reset = adapter checkpoints gone. Always upload to HF as part of training.
- Network reachability fails silently mid-download. Always `ls -la` the download dir
  before assuming the pull succeeded.
- `pip install` failures during a run will retry network endlessly. Pre-install
  ALL deps before running anything important.
- `pip install protobuf sentencepiece` needed for Qwen tokenizers — add to preflight.
- HF download needs the right subfolder name. List the repo first
  (`hf repo files Omnisensai/arc-lora-run2`) before downloading.
- `hf download` with multiple `--include` flags = multiple flags, not one comma-separated.
- The pod's CWD is usually `/workspace`, but the repo is `/workspace/ARC-AGI2`.
  cd into the repo before running ANY script with relative paths.

### 2.8 Long-running jobs: tmux + background

Always run multi-hour evals in tmux:
```bash
tmux new -s eval
# in tmux:
python3 eval_script.py --limit 100  # 30-60 min
# Ctrl+B, then D to detach
# tmux a -t eval  to reattach
```

For parallel runs on multi-GPU pods: one tmux session per GPU, `CUDA_VISIBLE_DEVICES=0`
in window 1 and `CUDA_VISIBLE_DEVICES=1` in window 2. Don't try to "share" one GPU
between two models — they just time-share and finish in the same total wall time
as sequential.

### 2.9 Debugging order of operations

When a run produces garbage output:
1. **Print the actual prompt.** Print 1 puzzle's full prompt. Read it. Does it
   match what training used? If no, you're done debugging — fix the prompt.
2. **Print the raw model_output_raw** (not extracted_code). The raw shows what
   the model literally emitted including any Chinese, hallucinated metadata,
   structural collapses.
3. **Run at T=0 (greedy)** to remove sampling noise. If T=0 produces clean Python
   that's just wrong, sampling was a red herring. If T=0 still produces garbage,
   suspect precision/attention drift.
4. **Check pip versions vs training-time versions.** torch, transformers, peft,
   flash-attn, axolotl. Diff against training environment.
5. **Verify the adapter actually loaded.** Sometimes PEFT loads silently with
   wrong adapter or wrong target modules. Print `model.peft_config` and check
   modules_to_save / target_modules / rank.
6. **Self-consistency test.** Ask the model to write a solver for puzzles it was
   trained on. Run that solver against the same training pairs it saw. If it
   can't reproduce them, rule extraction is broken at training time, not at
   inference time.

This is the order. Each step is faster than the next. Don't skip 1 to debug 3.

---

## 3. Specific commits / artifacts referenced

- V1 (24% held-out) — `outputs/phase2_code` adapter, uploaded to
  `Omnisensai/arc-lora-run2/phase2_code`
- V1 training config — `Fine Tune Run 2/phase2_code_axolotl.yaml`
- V1 eval script — `Fine Tune Run 2/run_phase2_eval_local.py`
- V2 training config — `Phase2_V2/run1/*.yaml`
- V2 eval scripts — `Phase2_V2/run1/run_bucket1_eval_hf.py`,
  `Phase2_V2/run1/baseline_eval.py`,
  `Phase2_V2/run1/test_solve_self_consistency.py`
- Baseline raw outputs (20 puzzles) — `Phase2_V2/eval20_qwen_base.md`,
  `Phase2_V2/eval20_qwen_coder.md`

---

## 4. V2.1 plan (what we'd do next)

Based on tonight's findings:

1. **Base**: Qwen2.5-Coder-7B-Instruct (free output discipline)
2. **Phase 1**: Full substrate-literacy chain
   (`same_lit → diff_lit → same_rule → diff_rule → mixed`),
   ~5K records per stage, lr=0.00012, wd=0.01, seqlen=8192
3. **Phase 2**: Code training with cleaned canonical solvers
   - Strip 192 docstring puzzle-ID leaks
   - LoRA rank 64 (up from 32 in V2)
   - lr=0.00012, wd=0.01 (V1's recipe)
   - sample packing, train_on_inputs=false
4. **Eval discipline**:
   - Pin SYSTEM, render_pairs, chat template in a single shared module
   - Save tokenizer alongside every checkpoint
   - Save `pip freeze` alongside every checkpoint
   - Smoke-test with `--limit 1` BEFORE every 100-puzzle run
5. **Preflight checklist** before any training run:
   - [ ] Leak scan on training data (no puzzle IDs in targets)
   - [ ] Preflight one batch through the model, decode it, eyeball the format
   - [ ] Confirm chat template + apply_chat_template produces the expected prompt
   - [ ] Confirm tokenizer round-trips a sample prompt without warnings
   - [ ] Confirm eval script imports SYSTEM from the same module as training

---

*End of lessons. If a future session contradicts any of these, update the doc —
don't rediscover the lesson the hard way again.*
