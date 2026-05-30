# V2.1 Plan — Pre-Commitment Experimental Discipline

**Status**: pre-training plan. Committed BEFORE any V2.1 training starts so we
have a record of what we're testing, what would confirm/falsify, and what we
agreed counts as success.

**Date**: 2026-05-30

---

## Why this doc exists

V1 ran with rigorous splits, hit 24% on held-out. V2 ran ad hoc — we changed
multiple things at once (skipped Phase 1, new prompt format, different
hyperparams, new data), can't isolate what broke. V2.1 will be rigorous so the
next time we get a number, we know what produced it.

---

## 1. Data preparation (BEFORE any training starts)

### 1.1 Strip the canonical solver leaks

Every training target (canonical solver `.py` file) must pass these checks:

- [ ] No puzzle-ID string anywhere (regex: `[0-9a-f]{8}` matched against known
      puzzle IDs). Found in **192/740 V1 solvers** as docstrings.
- [ ] No literal grids (list of lists of integers, > 12 cells) that match any
      puzzle's input or output exactly.
- [ ] No metadata tags ("origin:", "puzzle_id:", "stage:", "generated_by:")
- [ ] No comments referencing specific puzzles by name

Write `Phase2_V2.1/scripts/clean_canonical_solvers.py` that:
1. Reads every `.py` in `canonical/solvers/`
2. Runs AST audit + regex scan
3. Strips docstrings, comments matching leak patterns
4. Writes to `canonical/solvers_clean/`
5. Reports per-file what was stripped
6. Refuses to write a file where leak couldn't be fully removed (flag for manual)

### 1.2 Validate every solver works on its puzzle

Some canonical solvers may have bugs (manual writing, edge cases). For each
`<pid>.py` in `solvers_clean/`:

- [ ] `exec()` the solver
- [ ] Run `solve(train_pair.input)` for every training pair → must == train_pair.output
- [ ] Run `solve(test_pair.input)` → must == test_pair.output

Solvers that don't pass all pairs are EXCLUDED from training data, not training
silently on wrong code. Write `Phase2_V2.1/scripts/validate_canonical_solvers.py`
that produces:
- `solvers_validated/` — passing solvers only
- `solvers_validation_report.json` — which failed and why

This is non-negotiable. Training on broken solvers teaches broken patterns.

### 1.3 Pin the prompt and tokenizer modules

Create `Phase2_V2.1/shared/prompts.py`:
```python
SYSTEM = "..."         # the V2.1 SYSTEM string
def render_pairs(...)   # the V2.1 pair format
def build_user_prompt(puzzle):  # the full USER assembly
```

Both training data builders (`build_phase1_*.py`, `build_phase2_code.py`) and
eval scripts (`eval_*.py`) MUST `from shared.prompts import SYSTEM, render_pairs`.

Pin the tokenizer: save `Qwen/Qwen2.5-Coder-7B-Instruct` tokenizer files into
every adapter directory at training-save time. Eval scripts load tokenizer from
the adapter dir, not from HF.

### 1.4 Pre-register the splits

Pick splits BEFORE training. Write them to `Phase2_V2.1/splits/` and commit:
- `train_puzzles.txt` — N puzzles used in training (any/all stages)
- `dev_eval_puzzles.txt` — held-out, can be eval'd during development
- `frozen_final_puzzles.txt` — **NEVER LOOKED AT** until V2.1 is declared done

Final number from V2.1 = solve rate on `frozen_final_puzzles.txt`. Cannot be
re-rolled. Cannot be "selected" by eyeballing dev results.

---

## 2. Training chain (V2.1 recipe)

```
Base: Qwen2.5-Coder-7B-Instruct       (output discipline for free)
   │
   ├─ Stage 1a: phase1_same_lit       ← T encode/decode, same-size
   │  • lr=0.00012, wd=0.01, seqlen=8192, rank=64
   │  • save: outputs/v21_1a
   │  • eval: substrate literacy probe on dev set (§3.2)
   │
   ├─ Stage 1b: phase1_diff_lit       ← T encode/decode, diff-size
   │  • lora_model_dir=outputs/v21_1a
   │  • save: outputs/v21_1b
   │  • eval: substrate literacy probe
   │
   ├─ Stage 1c: phase1_same_rule      ← apply rule to new input, same-size
   │  • lora_model_dir=outputs/v21_1b
   │  • save: outputs/v21_1c
   │  • eval: substrate literacy probe
   │
   ├─ Stage 1d: phase1_diff_rule      ← apply rule to new input, diff-size
   │  • lora_model_dir=outputs/v21_1c
   │  • save: outputs/v21_1d
   │  • eval: substrate literacy probe
   │
   ├─ Stage 1e: phase1_mixed          ← grab-bag, all substrate tasks
   │  • lora_model_dir=outputs/v21_1d
   │  • save: outputs/v21_1e
   │  • eval: substrate literacy probe + full prompt smoke test
   │
   └─ Stage 2:  phase2_code           ← write def solve given pairs
      • lora_model_dir=outputs/v21_1e
      • save: outputs/v21_final
      • eval: solve rate on dev_eval (NOT frozen) + leak audit on outputs
```

### Hyperparameters (pinned)
| Param | Value | Source |
|---|---|---|
| base_model | Qwen2.5-Coder-7B-Instruct | V2.1 finding |
| learning_rate | 0.00012 | V1 |
| weight_decay | 0.01 | V1 |
| sequence_len | 8192 | V1 |
| lora_rank | 64 | V2.1 bump from V1's 32 |
| lora_alpha | 128 (2× rank) | standard |
| sample_packing | true | V1 + V2 |
| train_on_inputs | false | V1 + V2 |
| attn_implementation | flash-attn | training |
| seed | 42 | pin this |

---

## 3. Evaluation discipline

### 3.1 Three eval levels
1. **Substrate literacy probe** (after each Phase 1 stage) — tests "did the model
   learn THIS phase's specific skill?" Small (50 examples), fast (~1 min).
2. **Dev eval** (after each major checkpoint) — solve rate on
   `dev_eval_puzzles.txt`. Can be looked at, used for go/no-go decisions.
3. **Frozen final eval** (ONCE at the end) — solve rate on
   `frozen_final_puzzles.txt`. The number we report. Single shot. No re-runs.

### 3.2 Substrate literacy probes — what each one checks

| Phase | Probe |
|---|---|
| 1a same_lit | Given INPUT + OUTPUT (same-size), emit T. Check T == expected_T (string match). |
| 1b diff_lit | Given INPUT + OUTPUT (diff-size), emit T facts. Check facts match expected. |
| 1c same_rule | Given INPUT + T + new INPUT, emit new OUTPUT. Same-size. Check grid match. |
| 1d diff_rule | Same as 1c but diff-size. |
| 1e mixed | Random sampling from 1a-1d probes. |

Each probe is a SEPARATE jsonl with prompt + expected. Run with greedy, score
exact match. Save to `Phase2_V2.1/eval/<stage>_probe_results.jsonl`.

Critical for diagnosis: if Stage 1c probe score is high but Stage 2 (code) solve
rate is low, the substrate works but the code-emission step is broken. If
Stage 1c probe is low, fix the substrate before going to code.

### 3.3 Per-checkpoint metric panel

For every saved checkpoint, log to `metrics_panel.csv`:
- step, epoch, train_loss, eval_loss
- substrate probe score (current stage)
- dev_eval solve rate (sampled subset, fast)
- per-mode tally: PASS / WRONG_OUTPUT / SHAPE_MISMATCH / RUNTIME_ERROR /
  EMPTY_OR_INVALID / HARDCODED

Look at the trajectory across the panel BEFORE selecting a final checkpoint.

---

## 4. Ablations — what we'd actually run

Pre-commit to which ablations matter. Order by expected information gain:

### 4.1 Must run (defines V2.1's identity)
- [ ] **V2.1 full**: base=Coder, Phase 1 chain, Phase 2 code (the main run)
- [ ] **V2.1 minus Phase 1**: base=Coder, skip Phase 1, only Phase 2 code
  - **predicts**: if methodology holds, this scores < V2.1 full
  - **falsifies**: if this matches V2.1 full, Phase 1 was unnecessary
- [ ] **V2.1 from Base Qwen**: base=Qwen-7B-Instruct, Phase 1 chain, Phase 2 code
  - **predicts**: if Coder-vs-Base finding holds, this < V2.1 full
  - **falsifies**: if this matches V2.1 full, Coder wasn't necessary

### 4.2 Run if time permits
- [ ] **V2.1 leak-not-stripped**: train on dirty canonical solvers (with leaks)
  - **predicts**: dev_eval similar, frozen_final much worse (leak doesn't help OOD)
- [ ] **V2.1 lower rank (32)**: same chain, rank=32 not 64
  - **predicts**: similar dev_eval, slightly worse frozen_final
- [ ] **V2.1 longer training**: 2× epochs on each stage
  - **predicts**: maybe better, maybe overfit; settles the lr/epochs question

### 4.3 Will NOT run (decided in advance)
- Different prompt formats — pin V2.1 prompts, don't bikeshed
- Different LoRA targets — use V1's targets
- Different base models beyond Coder/Base — narrow the question

---

## 5. Checkpoint policy

- Save every 1000 steps during each stage.
- Keep ALL checkpoints until run is fully evaluated. Disk is cheap.
- At end of each stage, identify the checkpoint with best substrate probe score
  and tag it as the "promoted" checkpoint for next stage init.
- Upload promoted checkpoints to HF: `Omnisensai/arc-lora-v21/<stage>`.
- Save `pip freeze`, `nvidia-smi`, axolotl config, tokenizer, and chat template
  into every promoted checkpoint dir. Reproducibility tax.

---

## 6. Failure recovery protocol

When something breaks (training NaNs, eval shows garbage, etc.), follow
SFT_Lessons §2.9 in ORDER:

1. Print the actual prompt being sent. Eyeball it.
2. Print raw model output (not extracted). Eyeball it.
3. Run at T=0 to remove sampling noise.
4. Check pip versions vs training versions.
5. Verify adapter loaded with `print(model.peft_config)`.
6. Self-consistency test on training puzzles.

Do NOT change two things at once. Do NOT skip step 1 because "the prompt is
obviously right." Most of the V2 night was wasted because we did both.

---

## 7. Definition of done

V2.1 is "done" when:
- All Phase 1 stages have substrate probe scores ≥ 80%
- Phase 2 dev_eval solve rate is measured and stable across two seeds
- Frozen final eval is run ONCE and the number is what we report
- All artifacts uploaded to HF (`Omnisensai/arc-lora-v21/*`)
- This doc has a "Results" section appended with actual numbers

The number we publish is the frozen final score. No re-rolls. No "we found a
bug and ran again." If we find a bug after the frozen run, that's V2.2.

---

## 8. Open questions to resolve before training

These need answers before we start. Each gets a quick decision now.

- [ ] **Phase 1 dataset size**: V1 used ~5K records per stage. Same? Bigger?
- [ ] **Augmentation policy**: D4 × color permutation = 42 variants per puzzle.
      Apply to substrate stages too, or only code stage?
- [ ] **Frozen final split size**: V1 used 30 puzzles (frozen_final_eval_ids).
      For V2.1, do we want larger (100+) for tighter CI on the headline number?
- [ ] **Eval temperature**: T=0.5 default. Pin it. Same T for all probes + dev +
      frozen.
- [ ] **pass@N**: V1 used pass@2. V2 used pass@1. Pin one (pass@1 for cleanliness,
      pass@2 if we want to show methodology variance).

---

## Status checklist

### Pre-training
- [ ] Data prep (§1) complete
- [ ] Prompt module pinned (§1.3)
- [ ] Splits committed (§1.4)
- [ ] Probes generated (§3.2)
- [ ] Open questions §8 resolved

### Training
- [ ] Stage 1a complete + probe ≥ 80%
- [ ] Stage 1b complete + probe ≥ 80%
- [ ] Stage 1c complete + probe ≥ 80%
- [ ] Stage 1d complete + probe ≥ 80%
- [ ] Stage 1e complete + probe ≥ 80%
- [ ] Stage 2 complete + dev_eval measured

### Ablations (§4.1)
- [ ] V2.1 full
- [ ] V2.1 minus Phase 1
- [ ] V2.1 from Base Qwen

### Final
- [ ] Frozen eval run ONCE
- [ ] Results appended to this doc
- [ ] Artifacts uploaded to HF
