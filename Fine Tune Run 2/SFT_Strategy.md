# SFT Strategy — Fine Tune Run 2

The plan for the second supervised fine-tuning run, including the
two-phase curriculum, splits, hold-out discipline, substrate
specifications, and per-phase training-data format.

This document is the **strategy** layer. Parameters (mix ratios, LR,
seeds) are locked in the YAML configs alongside this file
(`phase1a_config.yaml`, `phase1b_config.yaml`, etc.). When this doc and
a config disagree, the config wins for execution and this doc gets
updated to match.

---

## 1. Overview — Two-phase curriculum

Run 2 trains in two phases with two distinct goals:

| Phase | Goal | Targets |
|---|---|---|
| **Phase 1: Transformation grid literacy** | Teach the model to *see* the input→output transformation as a structured object (the "substrate"). No code generation. | Substrate fields and output grids. |
| **Phase 2: Coding + debug** | Teach the model to emit `def solve(input_grid)` Python that produces the correct output, and to repair its own wrong code given validator feedback. | Python functions. |

The previous run (Run 1, commit `268648f` and earlier) hit 18% pass@1 /
24% pass@2 on a clean held-out — with only **1 correct code per puzzle
and 10 wrong** in the training mix, and the "solve" task only 8% of the
mix. That result establishes the thesis: substrate-flavored SFT
transfers. Run 2 builds on it with:

1. A **curriculum** (Phase 1 → Phase 2) instead of one mixed run.
2. **Strict held-outs** (60 A2E puzzles never touched) instead of the
   ad-hoc Run 1 splits.
3. **Disciplined task mix** in each phase.
4. A **per-pair substrate** (`encode_auto`) that handles diff-size
   puzzles natively, not just same-size.

---

## 2. Splits & hold-out discipline

The split policy is the single most important non-architectural choice
in this run. We deliberately overweight clean evaluation over training
volume.

### 2.1 A2E partitioning (114 content-unique puzzles)

Of the 120 A2E files, 6 also exist in A1 (the "leakers" identified in
`puzzles/README.md`). They are tracked as a separate bucket. The
remaining **114 A2-only A2E puzzles** are split three ways:

| Split | Count | Role |
|---|---|---|
| `a2e_train_hard` | 50 | Trained on with aggressive augmentation. |
| `a2e_dev_hard` | 30 | Checkpoint selection during training. Light augmentation. |
| `a2e_final_hard` | 34 | **Frozen.** Touched exactly once at the end of each run. No augmentation. |
| `a2e_leakers` | 6 | Excluded from hard-dev and final. May enter train **only** if the corresponding A1 version is also seen in train (else mark as A2-train-only). |

`a2e_final_hard` is the headline number. If accidentally touched
(generation bug, eval leakage into train), regenerate from a fresh
random seed and re-roll all three A2E buckets. We are willing to lose
training data to keep the frozen 34 clean.

### 2.2 Train pool

Every other content-unique puzzle (~1027 after dedup) lives in the
training pool: A1T + A1E + A2T + the 6 A2E leakers, deduped by
canonical content. This pool gets the full augmentation stack.

### 2.3 Hold-out unit

**Hold-outs are by augmentation parent, not by example.** Every
augmented variant of a held-out puzzle is held out. The split unit is
the (dedup-cluster, puzzle-id) pair: if puzzle `abc12345` is in
`a2e_final_hard`, then no D4 rotation, color permutation, or pair
subset of `abc12345` may appear anywhere in train.

The augmentation seed is per-puzzle so the held-out check is trivially
verifiable: "did this puzzle id appear in train under any
augmentation?" → grep the manifest.

### 2.4 Stratification

The 50/30/34 cut is **stratified** across three axes so the three
buckets remain comparable:

- Size bucket: small (≤ 6×6), medium (≤ 15×15), large (> 15×15)
- Pair-shape mix: all-S, all-D, mixed
- Test-pair count: 1 vs ≥ 2

Random tie-breaking inside each stratum. Seed recorded in the config.

---

## 3. Augmentation policy

ARC's rule-preserving augmentations are well-studied: D4 symmetries and
color permutations leave the underlying rule intact, so they generate
fresh surface forms with identical semantic content. The Run 1 result
(18% from a thin mix) tells us volume is not the bottleneck — task
diversity and mix discipline are. We keep augmentation modest.

| Bucket | D4 | Color perms | Pair subsetting |
|---|---|---|---|
| Train (pool + `a2e_train_hard`) | all 8 | 3 random | yes (1–3 of N train pairs) |
| `a2e_dev_hard` | all 8 | 1 random | no |
| `a2e_final_hard` | identity only | none | no |

Rules:

- Pair-subsetting subsets **train pairs only**, never test pairs.
- Subset size ≥ 1. T4 additionally requires ≥ 2 remaining train pairs
  (it needs N-1 worked examples plus 1 cold).
- Every example records its parent puzzle id, D4 op, color-perm seed,
  and subset ids in the manifest. This is what makes hold-out
  verification a one-line check.

Approximate per-puzzle augmentation budget: 8 × 3 × 4 (subset draws) ≈
100 variants. Times 6 tasks ≈ 600 examples per source puzzle in Phase
1. Across the ~1077 trainable puzzles, that's roughly 600k examples —
in the same order of magnitude as Run 1, with much better mix
discipline.

---

## 4. Phase 1 — Transformation grid literacy

### 4.1 Why two sub-phases (1.A and 1.B)

Phase 1 teaches two distinct skills that are easy to confuse:

- **Substrate literacy:** given a single pair, encode/decode it
  mechanically. Roughly "1:1 mapping."
- **Rule induction:** given several pairs, generalize the
  transformation and apply it to a new input. Multi-pair reasoning.

Mixing them from step 0 means the loss on rule-induction tasks confounds
both errors. Phase 1.A teaches the atomic substrate skill alone; Phase
1.B builds rule-induction on top.

### 4.2 Task tags

| Tag | Context | Target | Sub-phase |
|---|---|---|---|
| `T1` | 1 pair: (input, output) | substrate for that pair | 1.A |
| `T2` | 1 pair: (input, write-substrate) | output | 1.A — *same-size only* |
| `T3` | all train pairs: (input, output) | substrate per pair | 1.A |
| `T4` | N-1 worked pairs + 1 cold pair input | substrate for the cold pair | 1.B |
| `T5` | all train pairs + test input | **test substrate** | 1.B |
| `T6` | all train pairs + test input | test output grid | 1.B |

**Per-task pair dispatch:**

- `T2` requires the *lossless* same-size pixel substrate (because that
  is the only substrate form with a decoder). For mixed-shape puzzles,
  T2 emits examples only for the same-size pairs and skips the diff-
  size ones.
- All other tasks use `encode_auto`, which dispatches per pair to the
  appropriate substrate (pixel for same-size, aggregate for diff-size).
  Both substrate forms are valid prediction targets.

### 4.3 Phase 1.A — substrate literacy

Train **from the base Qwen-2.5-7B-Instruct checkpoint** on T1 + T2 +
T3 only. The target mix:

| Task | Mix share |
|---|---|
| T1 | 40% |
| T2 | 35% |
| T3 | 25% |

T2 is intentionally heavily weighted: it forces the model to learn the
*decoding* direction, which is the harder half of the substrate
relationship. T3 introduces multi-pair input but with mechanical
per-pair targets — still "literacy," just batched.

**Probe / stopping criterion:** before kicking off 1.B, hold out a small
set (~50 puzzles from the train pool, never seen during 1.A) and
measure substrate-prediction exact-match accuracy on T1. The "1.A done"
threshold is ≥ 95% on same-size pairs and ≥ 90% on diff-size pairs.
Below that, 1.B will compound errors.

Save the 1.A LoRA as `outputs/phase1a/...` (path TBD by training
script).

### 4.4 Phase 1.B — rule application

Continue from the 1.A LoRA. Train on T4 + T5 + T6 with a small carry of
T1 + T2 + T3 to prevent catastrophic forgetting of the atomic skill.

| Task | Mix share |
|---|---|
| T1 | 5% (carry) |
| T2 | 5% (carry) |
| T3 | 10% (carry) |
| T4 | 25% |
| T5 | 40% |
| T6 | 15% |

T5 — "given the worked pairs and the test input, predict the test
substrate" — is the load-bearing bridge task between substrate literacy
and full output prediction. It puts the loss signal where the *rule*
lives (the substrate target) rather than diluting it across an entire
output grid where most cells are trivial copies of the input.

### 4.5 Eval protocol (Phase 1)

Protocol C, with per-test-pair dispatch. ARC's official scoring rule
applies: every test pair in a puzzle must be exactly correct for that
attempt to count.

For each test pair:

- **Same-size pair**:
  - Attempt 1: predict `write` substrate → mechanically `decode` →
    output.
  - Attempt 2: predict output directly.
- **Diff-size pair**:
  - Attempt 1: predict `struct` substrate as a CoT prefix, then
    continue generating the output.
  - Attempt 2: predict output directly with no substrate prefix.

Puzzle is counted as solved if any single attempt path produces the
correct output for *all* test pairs.

Decode: greedy (`temperature = 0.0`) for the headline number; sampled
variants reported as ablations.

Reporting on `a2e_final_hard`:

- `pass@2` (headline)
- substrate-path solve rate
- direct-path solve rate
- both-paths solved
- neither-path solved
- stratified by size bucket and S/D mix

---

## 5. Phase 2 — Coding + debug

High-level only at this stage; detailed spec will land before Phase 2
training starts.

### 5.1 What changes from Run 1

Run 1's Phase 2-style data had **1 correct code + 10 wrong code per
puzzle**, and the "solve" task was 8% of the mix. The thin positive
signal capped what the model could learn. Phase 2 of Run 2:

1. **Multiple valid programs per puzzle.** Different algorithms that
   produce the same correct output. With D4 augmentation, each
   augmented variant generates a fresh program too.
2. **Balanced mix.** The "solve correctly" task lifted to ~40% of the
   mix instead of 8%.
3. **Substrate-aware code.** Programs may reference substrate fields
   produced by Phase 1 (e.g. operate on the cell-changed-set rather
   than the full grid), shrinking the search space.

### 5.2 Tasks (provisional)

| Tag | Context | Target |
|---|---|---|
| `T7` | train pairs + substrates + test substrate | `def solve()` Python |
| `T8` | raw puzzle (no substrate scaffold) | substrate blocks + `def solve()` |
| `T9` | wrong code + validator feedback | corrected code |

Phase 2 mix and weighting TBD pending Phase 1.B results.

### 5.3 Eval

Same `a2e_final_hard` set, same scoring rule. Phase 2 success is
measured as `pass@2` exact-output-match on the frozen 34, with model
emitting code that we run inside the validator. This is the headline
ARC number.

---

## 6. Substrate specification

The substrate is the structured object that bridges raw grids and
Python code. It is the shared vocabulary between Phase 1 (literacy) and
Phase 2 (codegen). Two flavors, dispatched per pair by
`substrate.encode_auto(inp, out)`.

### 6.1 Same-size pixel substrate (write field)

**When:** `input.shape == output.shape`.
**Implementation:** `substrate.encode(inp, out)` →
`List[List[str]]` (a grid of single-character strings).
**Decoder:** `substrate.decode(inp, substrate) -> output`. Lossless.

**Legend:**

| Symbol | Meaning |
|---|---|
| `.` | cell preserved: `input[r,c] == output[r,c]` |
| `0`–`9` | cell changed: output cell takes this color value |

**Round-trip invariant:** `decode(inp, encode(inp, out)) == out` for any
same-size pair.

**Example.** Input (3×3): a single off-center pixel becomes a cross.

```
input    output    substrate
000      010       .1.
010  →   111   →   1.1
000      010       .1.
```

The substrate immediately shows the four cells that were filled in
(`1`'s in the corners are absent; only edge-center cells `.1.` change),
and the unchanged center (`1` → `.`). The model reads "fill the four
edge-center neighbors of any 1" as the rule.

### 6.2 Diff-size aggregate substrate (struct field)

**When:** `input.shape != output.shape`.
**Implementation:** `substrate.diffsize_encode(inp, out) -> str`.
**No decoder.** Lossy by design.

**Format** (sections separated by blank lines, order is fixed):

```
SIZE <H>x<W> -> <h>x<w>   h:<rel> w:<rel>
BG <in_bg> -> <out_bg>   <rel>

PALETTE
  <color> <in_count> -> <out_count> <rel>
  ...

ROWS
  IN_DOM:  <per-row input dominants>
  OUT_DOM: <per-row output dominants>
  IN_NZ:   <per-row input non-bg counts>
  OUT_NZ:  <per-row output non-bg counts>

COLS
  IN_DOM:  <per-col input dominants>
  OUT_DOM: <per-col output dominants>
  IN_NZ:   <per-col input non-bg counts>
  OUT_NZ:  <per-col output non-bg counts>

BBOX
  <color> in:<bbox> out:<bbox>
  ...
```

**`relate(a, b)` tag legend** (used in SIZE, BG, PALETTE rows):

| Tag | Meaning | Condition |
|---|---|---|
| `=` | identical | `a == b` (or both zero) |
| `×N` | scaled up by N | `b == a*N`, integer `N > 1` |
| `÷N` | scaled down by N | `a == b*N`, integer `N > 1` |
| `Δ±N` | additive shift | no integer ratio applies |
| `new` | appeared from zero | `a == 0`, `b > 0` |
| `dropped` | gone to zero | `a > 0`, `b == 0` |

Multiplicative-before-additive is intentional: `relate(1, 2) = ×2`, not
`Δ+1`.

**BBOX format:** `r<min_row>-<max_row>,c<min_col>-<max_col>` if the
color appears in that grid, `none` if absent.

**Sorting:** `PALETTE` and `BBOX` are sorted ascending by color value
(stability across pairs, not salience). `ROWS` and `COLS` preserve
natural order.

### 6.3 Documentation notes — do not patch these

- **`BG` is mechanical, not semantic.** It is the most-frequent color
  (ties broken by smaller numeric color). For some pairs it matches
  human intuition (color 0); for others it does not. That is correct
  behavior; do not patch with heuristics.
- **The diff-size substrate is lossy.** Two distinct grids can share
  the same aggregate substrate. The substrate provides evidence, not a
  reconstruction recipe.
- **T2 does not apply to diff-size pairs.** T2 requires the lossless
  pixel substrate; the dataset generator must filter diff-size pairs
  out of T2 examples.
- **`ROWS` / `COLS` can be long by design.** On a 30×30 input each
  produces 30 tokens. No truncation. The token cost buys spatial signal.

### 6.4 Worked diff-size examples

See `substrate.py` docstrings and `scripts/test_diffsize_substrate.py`
for the canonical examples. The regression test exercises three:
crop-like (4×5 → 2×2), tiling-like (2×2 → 6×6), and scalar selection
(3×3 → 1×1). A repo-wide sweep confirms all 5,786 real diff-size pair
instances encode without error.

---

## 7. Training data format

The Phase 1 generator emits JSONL records, one example per line:

```json
{
  "task": "T5",
  "stage": "phase1b",
  "prompt": "<assembled context, task-specific>",
  "target": "<assembled target, task-specific>",
  "provenance": {
    "puzzle_id": "00576224",
    "source": "A1E",
    "d4_op": "rot90",
    "color_perm_seed": 17,
    "pair_subset": [0, 2],
    "test_pair_index": 0
  }
}
```

The `provenance` block is what makes hold-out verification a one-line
grep. The `task` and `stage` fields are required so the trainer can
compute per-task validation loss (one of the Run 1 lessons:
aggregate val-loss hides which task is actually being learned).

Per-task prompt/target schemas (T1–T6) are codified in the dataset
generator; this doc describes intent, not byte-level format. The
canonical reference is the generator + a sample JSONL file checked
into `Fine Tune Run 2/data_sft/`.

---

## 8. Files

| Path | Purpose |
|---|---|
| `Fine Tune Run 2/SFT_Strategy.md` | this document |
| `Fine Tune Run 2/phase1a_config.yaml` | locked Phase 1.A parameters |
| `Fine Tune Run 2/phase1b_config.yaml` | locked Phase 1.B parameters |
| `Fine Tune Run 2/puzzles/` | input corpus (1920 files) |
| `Fine Tune Run 2/puzzles/README.md` | puzzle fact sheet |
| `Fine Tune Run 2/classify_origin.py` | content-unique origin classifier |
| `Fine Tune Run 2/data_sft/` | generated SFT training data |
| `Fine Tune Run 2/splits/` | locked train/dev/final puzzle id lists |
| `substrate.py` | substrate library (top of repo, shared) |
| `scripts/test_diffsize_substrate.py` | substrate regression test |

---

## 9. Open items (tracked here, not blocking)

- **Phase 1.A → 1.B probe spec.** Threshold values (95% / 90%) are
  reasonable starting points but not validated. Tune after the first 1.A
  run lands a real number.
- **Phase 2 task spec.** Provisional in §5. Lock before Phase 2 data
  generation.
- **TTT (test-time training).** Current SoTA on ARC includes per-puzzle
  fine-tuning at inference. Not part of Run 2, but the Phase 1 substrate
  vocabulary is a useful base for it later.
- **Mixed-pair puzzles.** 15 puzzles have S+D pair mixes. The generator
  handles them per-pair, but they're worth a manual audit pass once
  the first dataset lands.
