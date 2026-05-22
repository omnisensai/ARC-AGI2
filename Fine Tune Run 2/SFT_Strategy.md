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

## 0. Orientation — core thesis and failure taxonomy

### 0.1 Core thesis

LLMs always face the **grounding problem**: they cannot certify their
own truth. They can generate plausible patterns, code, substrates, and
explanations, but they cannot determine whether those outputs are
correct without an external check.

The architecture is therefore:

```
model proposes
  substrate constrains
  validator checks
  diff map localizes error
  model repairs
```

The substrate's role is to **narrow the search space**. Instead of
asking the model to learn

```
raw grid text  →  arbitrary code pattern
```

we ask it to learn

```
grid relation  →  transformation substrate  →  applied rule  →  output/code
```

This does not eliminate stochasticity — it makes stochastic navigation
happen inside a smaller, structured space.

- The substrate is **not** the reasoning engine.
- The model is **not** the truth engine.
- The validator remains the only authority.

### 0.2 Failure taxonomy

A raw code validator tells us only "the final code passed or failed."
It does not say *where* the system failed. Possible failure modes:

```
wrong rule
right rule but wrong substrate
right substrate but bad output
right output idea but bad code
valid code but wrong edge case
exec error
no grid returned
```

Phase 1 makes the first four layers measurable — that is its purpose.
Per-format probe accuracy maps directly onto the taxonomy:

| Probe format | Tests for |
|---|---|
| `pair_to_substrate` | "right substrate?" |
| `substrate_to_output` | "right decode?" |
| `all_pairs_to_substrates` | "right substrate, multi-pair?" |
| `cold_pair_to_substrate` | "right rule transfer?" |
| `test_substrate_prediction` | "right rule + apply?" |
| `direct_output_grid` | "right output?" |

Only after Phase 1 should Phase 2 ask "can it write code?" — and only
after Phase 2 should Phase 3 ask "can it repair from validator
feedback?"

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

### 4.1 One skill, one system message

Phase 1 trains **one unified skill**: infer and express the
transformation rule between ARC grids. We do *not* train the model to
recognize task labels like `T1`, `T2`, `T5`. Every Phase 1 record uses
the same system message:

```
Transformation Rule
```

The **field contract** in the user prompt — which trailing field the
prompt ends with — determines what the assistant must produce:

| User prompt ends with… | Assistant produces… |
|---|---|
| `SUBSTRATE:` | the substrate for the (input, output) pair shown |
| `OUTPUT:` | the output grid (from input + substrate, or from train pairs + test input) |
| `SUBSTRATES:` | per-pair substrates for every pair shown |
| `COLD SUBSTRATE:` | the substrate for the unseen cold pair |
| `TEST SUBSTRATE:` | the substrate for the test pair, inferred from the train pairs |

This is the single coherent transformation-rule language the model
learns. The six "task formats" below are internal bookkeeping for mix
ratios and per-task metrics; the model sees only the field contract.

Phase 2 and Phase 3 use their own system messages — `Code Solver` and
`Code Repair` respectively — because they're a different skill. Within
each phase, one system message.

### 4.2 Two sub-phases (1.A and 1.B) — why

Phase 1 teaches two distinct skills that are easy to confuse:

- **Substrate literacy:** given a single pair, encode/decode it
  mechanically. Roughly "1:1 mapping."
- **Rule induction:** given several pairs, generalize the transformation
  and apply it to a new input. Multi-pair reasoning.

Mixing them from step 0 means the loss on rule-induction tasks confounds
both errors. Phase 1.A teaches the atomic substrate skill alone; Phase
1.B builds rule-induction on top.

### 4.3 Phase 1 task formats

All six formats use the `Transformation Rule` system message. They
differ only in user-prompt structure and target field. The two columns
on the right show which sub-phase each format belongs to and the
per-pair substrate kind it requires.

| Internal label | User-prompt ends with | Target | Sub-phase | Per-pair dispatch |
|---|---|---|---|---|
| `pair_to_substrate` | `SUBSTRATE:` | substrate for that pair | 1.A | per pair via `encode_auto` |
| `substrate_to_output` | `OUTPUT:` | output grid | 1.A | **same-size pixel substrate only** |
| `all_pairs_to_substrates` | `SUBSTRATES:` | per-pair substrates for all train pairs | 1.A | per pair via `encode_auto` |
| `cold_pair_to_substrate` | `COLD SUBSTRATE:` | substrate for the cold pair | 1.B | per pair via `encode_auto` |
| `test_substrate_prediction` | `TEST SUBSTRATE:` | substrate for the test pair | 1.B | per pair via `encode_auto` |
| `direct_output_grid` | `OUTPUT:` | test output grid | 1.B | n/a (output is the target) |

`substrate_to_output` requires the lossless same-size pixel substrate
(because that is the only substrate form with a deterministic decoder).
For mixed-shape puzzles the generator emits this format only for the
same-size pairs and skips the diff-size ones.

All other formats use `encode_auto`, which dispatches per pair to the
appropriate substrate (pixel for same-size, aggregate for diff-size).
Both substrate forms are valid prediction targets in those formats.

The full conversation schema for each format — exact field labels,
target structure — is in §7.

### 4.4 Phase 1.A — substrate literacy

Train **from the base Qwen-2.5-7B-Instruct checkpoint** on the three
single-pair literacy formats only. Target mix:

| Format | Mix share |
|---|---|
| `pair_to_substrate` | 40% |
| `substrate_to_output` | 35% |
| `all_pairs_to_substrates` | 25% |

`substrate_to_output` is intentionally heavily weighted: it forces the
model to learn the *decoding* direction, which is the harder half of
the substrate relationship. `all_pairs_to_substrates` introduces
multi-pair input but with mechanical per-pair targets — still
"literacy," just batched.

**Probe / stopping criterion (1.A done signal):** before kicking off
1.B, hold out ~50 puzzles never seen during 1.A and measure exact-match
on each literacy task:

| Probe | Threshold |
|---|---|
| `pair_to_substrate` exact-match (same-size) | ≥ 95% |
| `pair_to_substrate` exact-match (diff-size) | ≥ 90% |
| `substrate_to_output` exact-match (same-size only) | ≥ 95% |
| `all_pairs_to_substrates` exact-match | ≥ 90% |

Below threshold, 1.B will compound errors — extend 1.A instead. Above
threshold, do **not** overtrain the alphabet; move to 1.B.

Save the 1.A LoRA as `outputs/phase1a/...` (path TBD by training
script).

### 4.5 Phase 1.B — rule application

Continue from the 1.A LoRA. Train the three multi-pair / inference
formats with a small carry of the 1.A formats to prevent catastrophic
forgetting of the atomic skill.

| Format | Mix share |
|---|---|
| `pair_to_substrate` | 5% (carry) |
| `substrate_to_output` | 5% (carry) |
| `all_pairs_to_substrates` | 10% (carry) |
| `cold_pair_to_substrate` | 25% |
| `test_substrate_prediction` | 40% |
| `direct_output_grid` | 15% |

`test_substrate_prediction` — "given the worked pairs and the test
input, predict the test substrate" — is the load-bearing bridge task
between substrate literacy and full output prediction. It puts the loss
signal where the *rule* lives (the substrate target) rather than
diluting it across an entire output grid where most cells are trivial
copies of the input.

### 4.6 Eval protocol (Phase 1)

Protocol C, with per-test-pair dispatch. ARC's official scoring rule
applies: every test pair in a puzzle must be exactly correct for that
attempt to count.

For each test pair:

- **Same-size pair**:
  - Attempt 1: `test_substrate_prediction` → mechanically `decode` →
    output.
  - Attempt 2: `direct_output_grid`.
- **Diff-size pair**:
  - Attempt 1: `test_substrate_prediction` as CoT prefix, then continue
    generating output (substrate diagnostic; not mechanically
    decodable).
  - Attempt 2: `direct_output_grid` with no substrate prefix.

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

Phase 2 uses its own system message:

```
Code Solver
```

A subsequent repair phase (Phase 3) uses:

```
Code Repair
```

One system message per phase — same principle as Phase 1.

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

### 5.2 Formats (provisional)

| Internal label | User prompt | Target |
|---|---|---|
| `substrate_to_code` | train pairs + substrates + test substrate | `def solve()` Python |
| `raw_to_substrate_plus_code` | raw puzzle (no substrate scaffold) | substrate blocks + `def solve()` |
| `repair_from_feedback` | wrong code + validator feedback | corrected code (Phase 3, `Code Repair`) |

Mix and weighting TBD pending Phase 1.B results.

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

### 7.1 Record envelope

Phase 1 records are JSONL, one example per line, in standard chat-message
format with a sibling `provenance` block for hold-out verification:

```json
{
  "messages": [
    {"role": "system",    "content": "Transformation Rule"},
    {"role": "user",      "content": "<assembled context, format-specific>"},
    {"role": "assistant", "content": "<target, format-specific>"}
  ],
  "provenance": {
    "format": "test_substrate_prediction",
    "stage": "phase1b",
    "puzzle_id": "00576224",
    "source": "A1E",
    "d4_op": "rot90",
    "color_perm_seed": 17,
    "pair_subset": [0, 2],
    "test_pair_index": 0
  }
}
```

The `messages` array is what the trainer reads. The `provenance` block
is metadata: most trainers ignore unknown top-level keys, and our
holdout-check and per-format validation-loss tracking depend on it. The
`format` and `stage` fields in particular must be set — the Run 1
lesson was that aggregate val-loss hides which format is actually being
learned.

### 7.2 The Transformation Rule system message

Every Phase 1 record uses:

```json
{"role": "system", "content": "Transformation Rule"}
```

No prose instructions, no examples in the system slot, no task IDs.
The user prompt's trailing field tells the model what to produce.

### 7.3 Field-contract conventions

User prompts assemble fields in a fixed grammar so the model can rely
on layout:

- **Pair labels:** `P1`, `P2`, `P3`, … in order of presentation.
- **Field labels (block-leading):** `INPUT:`, `OUTPUT:`, `SUBSTRATE:`,
  `SUBSTRATES:` (plural for the multi-pair format), `COLD INPUT:`,
  `COLD OUTPUT:`, `COLD SUBSTRATE:`, `TEST INPUT:`,
  `TEST SUBSTRATE:`.
- **Per-pair fields:** prefixed with the pair label and a space, e.g.
  `P1 INPUT:`, `P1 SUBSTRATE:`.
- **Block separator:** one blank line between fields. Field label and
  its content are separated by a single newline.
- **Grids** are rendered via `substrate.format_grid` — one row per
  line, one character per cell, no spaces, no commas.
- **Pixel substrates** render the same way (one character per cell,
  `.` and digits).
- **Aggregate substrates** render as the verbatim
  `diffsize_encode` output (multi-line text block).
- The user prompt **ends** with the field label whose value the
  assistant must produce, followed by a single newline. No content
  after that label.

### 7.4 The six formats

#### Format 1 — `pair_to_substrate`

**Purpose:** encode a single (input, output) pair as its substrate.

**User:**
```
INPUT:
<grid>

OUTPUT:
<grid>

SUBSTRATE:
```

**Assistant:** the substrate for that pair (pixel grid for same-size,
aggregate text block for diff-size).

**Sub-phase:** 1.A.

#### Format 2 — `substrate_to_output`

**Purpose:** apply a pixel substrate back to recover the output. Trains
the *decode* direction of the substrate relationship.

**Constraint:** same-size pixel substrate only. The generator must
skip diff-size pairs for this format. Diff-size aggregate substrates
are lossy and cannot mechanically reconstruct the output.

**User:**
```
INPUT:
<grid>

SUBSTRATE:
<pixel substrate>

OUTPUT:
```

**Assistant:** the output grid.

**Sub-phase:** 1.A.

#### Format 3 — `all_pairs_to_substrates`

**Purpose:** multi-pair substrate formatting with mechanical per-pair
targets. Still literacy, but at the puzzle level.

**User:**
```
P1 INPUT:
<grid>

P1 OUTPUT:
<grid>

P2 INPUT:
<grid>

P2 OUTPUT:
<grid>

SUBSTRATES:
```

**Assistant:**
```
P1 SUBSTRATE:
<substrate>

P2 SUBSTRATE:
<substrate>
```

**Sub-phase:** 1.A.

#### Format 4 — `cold_pair_to_substrate`

**Purpose:** analogy across pairs. Worked examples show the
input→output→substrate chain; the model must encode the cold pair's
substrate from its (input, output) alone, but with the rule context
the worked examples provide.

**User:**
```
P1 INPUT:
<grid>

P1 OUTPUT:
<grid>

P1 SUBSTRATE:
<substrate>

P2 INPUT:
<grid>

P2 OUTPUT:
<grid>

P2 SUBSTRATE:
<substrate>

COLD INPUT:
<grid>

COLD OUTPUT:
<grid>

COLD SUBSTRATE:
```

**Assistant:** the cold pair's substrate.

**Sub-phase:** 1.B. Requires ≥ 2 worked train pairs + 1 cold pair, so
puzzles with fewer than 3 train pairs (after subsetting) are skipped
for this format.

#### Format 5 — `test_substrate_prediction`

**Purpose:** the load-bearing bridge. Infer the transformation rule
from train pairs and apply it to the test input, expressing the answer
as substrate rather than output.

**User:**
```
P1 INPUT:
<grid>

P1 OUTPUT:
<grid>

P1 SUBSTRATE:
<substrate>

P2 INPUT:
<grid>

P2 OUTPUT:
<grid>

P2 SUBSTRATE:
<substrate>

TEST INPUT:
<grid>

TEST SUBSTRATE:
```

**Assistant:** the test pair's substrate.

**Sub-phase:** 1.B. Test pair's *output* is never shown in the prompt
— that's the whole point.

For same-size test pairs the predicted substrate is mechanically
decodable into the output. For diff-size test pairs the predicted
substrate is diagnostic / scaffold only.

#### Format 6 — `direct_output_grid`

**Purpose:** direct output prediction without substrate scaffolding.
Useful as attempt-2 in the eval protocol, but should not dominate
Phase 1 — the substrate path is the structured signal we want the
model leaning on.

**User:**
```
P1 INPUT:
<grid>

P1 OUTPUT:
<grid>

P2 INPUT:
<grid>

P2 OUTPUT:
<grid>

TEST INPUT:
<grid>

OUTPUT:
```

**Assistant:** the test output grid.

**Sub-phase:** 1.B.

### 7.5 Per-stage filenames

The dataset generator writes:

```
Fine Tune Run 2/data_sft/phase1a_train.jsonl
Fine Tune Run 2/data_sft/phase1a_dev.jsonl
Fine Tune Run 2/data_sft/phase1b_train.jsonl
Fine Tune Run 2/data_sft/phase1b_dev.jsonl
Fine Tune Run 2/data_sft/phase1_final_eval.jsonl
Fine Tune Run 2/data_sft/phase1_manifest.json
Fine Tune Run 2/splits/phase1_splits.json
```

`phase1_final_eval.jsonl` is the locked 34 — generated once, regenerated
only if the split seed changes (which itself is a deliberate decision,
not an automatic operation).

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
