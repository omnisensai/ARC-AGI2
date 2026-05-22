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
| `multi_pair_to_rule` | "right rule under multi-pair context?" |
| `test_substrate_prediction` | "right rule + apply (test pair)?" |
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
| `RULE:` | the rule (substrate) for the relevant pair |
| `OUTPUT:` | the output grid |

Two field labels for the assistant target. Which one the model
produces depends on which one the user prompt ends with. The five
"task formats" below are internal bookkeeping for mix ratios and
per-task metrics; the model sees only the field contract and the
trailing label.

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

All five formats use the same `Transformation Rule` system message.
They differ only in user-prompt structure and which field label the
prompt ends with. The two columns on the right show which sub-phase
each format belongs to and the per-pair substrate kind it requires.

| Internal label | User-prompt ends with | Target | Sub-phase | Per-pair dispatch |
|---|---|---|---|---|
| `pair_to_substrate` | `RULE:` | rule for the single pair shown | 1.A | per pair via `encode_auto` |
| `substrate_to_output` | `OUTPUT:` | output grid (reconstructed from input + rule) | 1.A | **same-size pixel substrate only** |
| `multi_pair_to_rule` | `RULE:` | rule for the trailing pair, given N-1 worked pairs | 1.B | per pair via `encode_auto` |
| `test_substrate_prediction` | `RULE:` | rule for the test pair, inferred from worked pairs | 1.B | per pair via `encode_auto` |
| `direct_output_grid` | `OUTPUT:` | test output grid | 1.B | n/a (output is the target) |

`substrate_to_output` requires the lossless same-size pixel rule
(because that is the only rule form with a deterministic decoder).
For mixed-shape puzzles the generator emits this format only for the
same-size pairs and skips the diff-size ones.

All other formats use `encode_auto`, which dispatches per pair to the
appropriate rule (pixel for same-size, aggregate for diff-size). Both
rule forms are valid prediction targets in those formats.

**`multi_pair_to_rule` position rotation:** for each augmented variant
of a puzzle with N train pairs, the generator emits N candidate items
— one per choice of which pair is the trailing one. This guarantees
systematic coverage of all positions across the training set, rather
than leaving it to random sampling.

Format disambiguation by structure (no special labels needed):

- `pair_to_substrate`: one (INPUT, OUTPUT) shown, trailing `RULE:`.
- `substrate_to_output`: one (INPUT, RULE) shown, trailing `OUTPUT:`.
- `multi_pair_to_rule`: N-1 worked (INPUT, OUTPUT, RULE) triples + 1
  pair with (INPUT, OUTPUT) but no RULE → trailing `RULE:`.
- `test_substrate_prediction`: N worked (INPUT, OUTPUT, RULE) triples +
  test pair with INPUT only → trailing `RULE:`.
- `direct_output_grid`: N (INPUT, OUTPUT) pairs + test INPUT only →
  trailing `OUTPUT:`.

The full conversation schema for each format is in §7.

### 4.4 Phase 1.A — substrate literacy

Train **from the base Qwen-2.5-7B-Instruct checkpoint** on the two
single-pair literacy formats only. Target mix:

| Format | Mix share |
|---|---|
| `pair_to_substrate` | 50% |
| `substrate_to_output` | 50% |

The two formats balance the *encode* and *decode* directions of the
substrate relationship. With one system message containing the legend,
the model learns the alphabet from English priors and uses these two
formats to ground it in concrete grid examples.

**Probe / stopping criterion (1.A done signal):** before kicking off
1.B, hold out 50 puzzles never seen during 1.A and measure exact-match
on each literacy task:

| Probe | Threshold |
|---|---|
| `pair_to_substrate` exact-match (same-size) | ≥ 95% |
| `pair_to_substrate` exact-match (diff-size) | ≥ 90% |
| `substrate_to_output` exact-match (same-size only) | ≥ 95% |

Below threshold, 1.B will compound errors — extend 1.A instead. Above
threshold, do **not** overtrain the alphabet; move to 1.B.

Save the 1.A LoRA as `outputs/phase1a_substrate_literacy/`.

### 4.5 Phase 1.B — rule application

Continue from the 1.A LoRA. Train the three multi-pair / inference
formats with a small carry of the 1.A formats to prevent catastrophic
forgetting of the atomic skill.

| Format | Mix share |
|---|---|
| `pair_to_substrate` | 5% (carry) |
| `substrate_to_output` | 5% (carry) |
| `multi_pair_to_rule` | 35% |
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

Every Phase 1 record uses the same system message — a compact legend
that defines the substrate alphabet and dispatch rule. Putting the
legend in the system prompt leverages Qwen's English pretraining
instead of forcing the model to learn the symbols by gradient descent.

Exact byte content (must match `EXPECTED_SYSTEM_MESSAGE` in
`verify_records.py`):

```
Transformation Rule

A RULE encodes one input/output grid transformation.

If input.shape == output.shape, the RULE is a same-shape grid:
  .       cell unchanged
  0-9     cell changed to this output color
Each cell is independent: RULE[r,c] depends only on input[r,c] and output[r,c],
not on neighbors.
Lossless: the output can be fully reconstructed from input + RULE.

If input.shape != output.shape, the RULE is an aggregate text block with sections
in this order: SIZE, BG, PALETTE, ROWS, COLS, BBOX. Sections are separated by
blank lines.
Whole-grid statistics — diagnostic only, not a per-cell reconstruction recipe.

Relation tags for numeric pairs a -> b:
  =        a == b
  ×N       b = a * N, integer N > 1
  ÷N       a = b * N, integer N > 1
  Δ±N      additive offset (b - a)
  new      a == 0 and b > 0
  dropped  a > 0 and b == 0
```

This is ~175 tokens, identical across every Phase 1 record (train, dev,
probe). With `train_on_inputs: false` the system tokens contribute zero
loss — pure context. The legend hits four pieces that the model would
otherwise have to discover from data: substrate alphabet (`.` and
`0-9`), section schema for diff-size, the relation tag table, and the
key invariants ("each cell independent," "lossless same-shape,"
"lossy diff-shape").

Phase 2 will use a different system message (`Code Solver`) with its
own legend describing `def solve(input_grid)` and friends. Phase 3
uses `Code Repair`. One system message per phase.

### 7.3 Field-contract conventions

User prompts assemble fields in a fixed grammar so the model can rely
on layout:

- **Field labels (block-leading):** `INPUT:`, `OUTPUT:`, `RULE:`. That
  is the entire label vocabulary. No per-pair prefixes (`P1`, `P2`),
  no special prefixes (`COLD`, `TEST`, `NEW`). Pairs are identified
  by structure (consecutive INPUT/OUTPUT/RULE triples) and the
  blank-line block separator.
- **Block separator:** exactly one blank line (`\n\n`) between blocks.
- **Label/content separator:** a single newline (`\n`) between a
  label and its content. The label includes the colon.
- **Grids** are rendered via `substrate.format_grid` — one row per
  line, one character per cell, no spaces, no commas.
- **Pixel rules** render the same way (one character per cell,
  `.` for unchanged and digits for changed).
- **Aggregate rules** render as the verbatim `diffsize_encode` output
  (multi-line text block starting with `SIZE …`).
- The user prompt **ends** with the field label whose value the
  assistant must produce, followed by a single newline. No content
  after that label. This is the "trailing-label" contract.

Disambiguation is purely structural. The model identifies which pair
is the "to-produce" one by counting blocks: it's the trailing pair,
i.e. the only one whose `RULE` (or `OUTPUT`) is missing content.

### 7.4 The five formats

#### Format 1 — `pair_to_substrate`

**Purpose:** encode a single (input, output) pair as its rule.

**User:**
```
INPUT:
<grid>

OUTPUT:
<grid>

RULE:
```

**Assistant:** the rule for that pair (pixel grid for same-size,
aggregate text block for diff-size).

**Sub-phase:** 1.A.

#### Format 2 — `substrate_to_output`

**Purpose:** apply a pixel rule back to recover the output. Trains
the *decode* direction of the substrate relationship.

**Constraint:** same-size pixel rule only. The generator skips
diff-size pairs for this format. Diff-size aggregate rules are lossy
and cannot mechanically reconstruct the output.

**User:**
```
INPUT:
<grid>

RULE:
<pixel rule>

OUTPUT:
```

**Assistant:** the output grid.

**Sub-phase:** 1.A.

#### Format 3 — `multi_pair_to_rule`

**Purpose:** rule transfer under multi-pair context. N-1 pairs are
shown fully worked (INPUT + OUTPUT + RULE); 1 trailing pair shows
INPUT + OUTPUT but no RULE — the model produces the trailing pair's
rule. The worked examples scaffold the format the model should
produce; the trailing pair's rule is still mechanically derivable from
the pair itself.

**Position rotation:** for each augmented variant of a puzzle with
N train pairs, the generator emits N candidate items — one per choice
of which pair is the trailing one. Sampling from the expanded pool
ensures every position gets coverage.

**User:**
```
INPUT:
<grid>

OUTPUT:
<grid>

RULE:
<rule>

INPUT:
<grid>

OUTPUT:
<grid>

RULE:
<rule>

INPUT:
<grid>

OUTPUT:
<grid>

RULE:
```

**Assistant:** the trailing pair's rule.

**Sub-phase:** 1.B. Requires ≥ 3 train pairs after subsetting (≥ 2
worked + 1 trailing). Records the position via
`provenance.trailing_pair_index`.

#### Format 4 — `test_substrate_prediction`

**Purpose:** the load-bearing bridge. Infer the transformation rule
from train pairs and apply it to the test input, expressing the
answer as rule (not output).

**User:**
```
INPUT:
<grid>

OUTPUT:
<grid>

RULE:
<rule>

INPUT:
<grid>

OUTPUT:
<grid>

RULE:
<rule>

INPUT:
<test input grid>

RULE:
```

**Assistant:** the test pair's rule.

**Sub-phase:** 1.B. The test pair shows INPUT only — its OUTPUT is
hidden (that's what makes it test-style). The model must infer the
rule from the worked pairs and apply it to the test INPUT.

For same-size test pairs the predicted rule is mechanically decodable
into the output. For diff-size test pairs the predicted rule is
diagnostic / scaffold only.

#### Format 5 — `direct_output_grid`

**Purpose:** direct output prediction without rule scaffolding.
Useful as attempt-2 in the eval protocol, but should not dominate
Phase 1 — the rule path is the structured signal we want the model
leaning on.

**User:**
```
INPUT:
<grid>

OUTPUT:
<grid>

INPUT:
<grid>

OUTPUT:
<grid>

INPUT:
<test input grid>

OUTPUT:
```

**Assistant:** the test output grid.

**Sub-phase:** 1.B.

### 7.5 The full tokenized record — what the model actually sees

Axolotl's `type: chat_template, chat_template: qwen2` applies Qwen2's
chat template to each `{messages: [...]}` record. The result is what
the model sees during training and what it must continue at inference.

**Template (Qwen2 ChatML-style):**

```
<|im_start|>system
{system_content}<|im_end|>
<|im_start|>user
{user_content}<|im_end|>
<|im_start|>assistant
{assistant_content}<|im_end|>
```

Special tokens: `<|im_start|>` and `<|im_end|>` are tokenizer-level
special tokens (single token each in Qwen2's tokenizer). They MUST NOT
appear inside any field content.

**Concrete example — `pair_to_substrate` record fully rendered** (the
system content has been abbreviated; the full ~175-token legend lives
inside the `<|im_start|>system ... <|im_end|>` block, see §7.2):

```
<|im_start|>system
Transformation Rule
…[full legend, see §7.2]…
  dropped  a > 0 and b == 0<|im_end|>
<|im_start|>user
INPUT:
022
022
200

OUTPUT:
022
022
100

RULE:
<|im_end|>
<|im_start|>assistant
...
...
1..<|im_end|>
```

Note carefully:

- A literal newline follows `<|im_start|>system`, then the system
  content (no trailing newline before `<|im_end|>`).
- The user content ends with `RULE:\n` (newline after the colon),
  then `<|im_end|>`. The trailing-label-plus-newline is the prompt's
  contract with the model.
- The assistant content starts immediately after
  `<|im_start|>assistant\n` and ends right before `<|im_end|>` — no
  extra leading or trailing whitespace.

**Loss masking:** `train_on_inputs: false` in the Axolotl config means
loss is computed **only on the assistant tokens** (everything between
`<|im_start|>assistant\n` and `<|im_end|>`, exclusive of the special
tokens themselves). The system and user blocks contribute no gradient.
Verified at inference time: the model is prompted with everything up
to and including `<|im_start|>assistant\n`, and must produce the rest.

**Inference prompt (greedy decode)** has the same shape, just stops
after `<|im_start|>assistant\n`:

```
<|im_start|>system
[full legend]<|im_end|>
<|im_start|>user
INPUT:
022
022
200

OUTPUT:
022
022
100

RULE:
<|im_end|>
<|im_start|>assistant
```

The model fills in the assistant content and emits `<|im_end|>` when
done. The probe harness (`run_probe.py`) compares the model's stripped
output against the expected assistant content for exact-match scoring.

**Anti-patterns to NOT do** (lessons applied from Run 1):

| Anti-pattern | Why it breaks |
|---|---|
| Putting task identifier (`T1`, `T5`, etc.) in the system message | Forces the model to learn artificial task identities; we want one unified skill. |
| Trailing whitespace on the user prompt's final label line (e.g. `RULE: \n`) | Tokenization may differ between train and inference; the model conditions on whitespace it doesn't see at inference. |
| Adding prose instructions (`identify the rule`) to the system message | Wastes context, biases the model away from the field contract. Note: the legend is *definition*, not instruction — it defines what symbols mean, not what the model should do. |
| Forgetting to set `train_on_inputs: false` | Loss gets computed on the prompt too, which is a much bigger signal than the target — drowns out the actual learning. |
| Different chat templates between train and inference | Qwen2 is finicky about exact token strings; only use `chat_template: qwen2` everywhere. |
| Inconsistent field labels across formats (e.g. `INPUT:` vs `Input:`) | Loss of structure; model has to handle case variation that conveys nothing. |
| Special tokens or `<|im_*|>` appearing in user-provided content | Confuses the chat template parser; can split records mid-content. |

**What the generator guarantees** (matches the above):

- System content is always identical to `EXPECTED_SYSTEM_MESSAGE` in
  `verify_records.py` (the full ~175-token legend, byte-for-byte).
- User content uses `\n\n` between blocks (one blank line). Block label and its data are separated by a single `\n`.
- Trailing field label has the form `LABEL:` (one of `INPUT:`,
  `OUTPUT:`, `RULE:`) followed by exactly one `\n`, no spaces.
- Grids are rendered with `substrate.format_grid` — one cell per character, one row per line, no spaces, no commas.
- Assistant content has no leading or trailing whitespace beyond what the substrate/grid renderer produces.
- No occurrences of `<|im_start|>`, `<|im_end|>`, or any other Qwen2 special token inside content.

These guarantees are enforced at generation time. The verification path
is to load any committed `.jsonl.gz` and `assert` the constraints — a
small `verify_records.py` script is a worthwhile addition if any of
the above ever drifts.

### 7.6 Per-stage filenames

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

## 9. Execution — LoRA chaining across stages and phases

The model goes through three distinct skill regimes (substrate
literacy, code generation, code repair). Default execution: **continue
the same LoRA within a phase; merge into the base model between
phases.**

### 9.1 Within-phase chain (no merge)

Phase 1.A → 1.B both train the **same LoRA adapter** with the same
system message (`Transformation Rule`):

```
Base Qwen2.5-7B-Instruct
  ↓ axolotl train phase1a_axolotl.yaml
outputs/phase1a_substrate_literacy/   (LoRA after 1.A)
  ↓ axolotl train phase1b_axolotl.yaml
  ↑ lora_model_dir: outputs/phase1a_substrate_literacy
outputs/phase1b_rule_application/     (same LoRA, more training)
```

Defensible because 1.A and 1.B are the same skill family and 1.B's mix
carries 10% of 1.A's formats to prevent forgetting (`pair_to_substrate`
5% + `substrate_to_output` 5%).

### 9.2 Cross-phase chain (merge between)

Between Phase 1 and Phase 2 we **merge** the Phase 1 LoRA into the
base model and train a **fresh** Phase 2 LoRA on the merged
checkpoint. Reasons:

- Phase 1 (`Transformation Rule`) and Phase 2 (`Code Solver`) are
  different skill families with different system messages and target
  vocabularies. Continuing the same LoRA risks catastrophic forgetting
  of substrate literacy when the code-generation loss takes over.
- Merge bakes the Phase 1 skill into base weights. Phase 2's LoRA only
  has to learn code, not "code while re-learning substrate."
- Cleaner ablations later: you can compare "raw base + Phase 2 LoRA"
  vs "Phase-1-merged + Phase 2 LoRA" to measure exactly what Phase 1
  contributed.
- Avoids LoRA stacking at inference (adapter ordering, serving
  compatibility, attribution complexity).

```
Base Qwen
  ↓ Phase 1.A + 1.B (LoRA continues across, no merge)
outputs/phase1b_rule_application/     LoRA adapter
  ↓ merge into base weights
outputs/phase1_merged/                full 7B model, ~15GB bf16
  ↓ Phase 2 trains fresh LoRA on phase1_merged
outputs/phase2_code_solver/           Phase 2 LoRA adapter
  ↓ merge into phase1_merged base
outputs/phase2_merged/                full 7B model
  ↓ Phase 3 trains fresh LoRA on phase2_merged
outputs/phase3_code_repair/           Phase 3 LoRA adapter
```

Disk note: each merged checkpoint is the full model (~15GB bf16).
We accept that cost.

### 9.3 Naming convention

| Output dir | What it is |
|---|---|
| `outputs/phase1a_substrate_literacy/` | LoRA adapter after 1.A |
| `outputs/phase1b_rule_application/` | LoRA adapter after 1.B (continues 1.A) |
| `outputs/phase1_merged/` | base + Phase 1 LoRA merged into one model |
| `outputs/phase2_code_solver/` | Phase 2 LoRA, trained on `phase1_merged` |
| `outputs/phase2_merged/` | `phase1_merged` + Phase 2 LoRA merged |
| `outputs/phase3_code_repair/` | Phase 3 LoRA, trained on `phase2_merged` |
| `outputs/phase3_merged/` | final deployable model |

### 9.4 What "merge" means operationally

For each merge step:

1. Load base (or previous merged) model.
2. Attach the most recent LoRA adapter via `peft.PeftModel.from_pretrained`.
3. Call `model = model.merge_and_unload()` — peft's standard merge.
4. Save: `model.save_pretrained(out_dir)` + tokenizer.

A short script will live at `Fine Tune Run 2/merge_lora.py` when Phase
1 is done. Not needed until then.

### 9.5 Decision points

- **After Phase 1.A:** Run probe. If thresholds pass, proceed to 1.B.
  If not, extend 1.A.
- **After Phase 1.B:** Run probe on `phase1b_probe.jsonl` to check
  literacy was preserved and rule-application accuracy is non-trivial.
  Then **merge** Phase 1 → `phase1_merged`.
- **Phase 2 onwards:** out of scope for Phase 1 documents — separate
  config + axolotl yaml + data generator will land when Phase 1 is
  validated end-to-end.

---

## 10. Lessons from Run 1 (Phase 2/3 implications)

A deep read of the Run 1 LoRA's generated Python code revealed a set of
recurring failure patterns. None of them block Phase 1, but every one
of them needs an explicit answer in Phase 2's training-data design.
Captured here so they survive the Phase 1 → Phase 2 transition.

### 10.1 Shape blind spot (highest-impact Phase 2 fix)

**Finding:** in 9 of 13 fully-failed Run 1 puzzles, the model's code
initialized the output at *input* dimensions and returned it unchanged,
even when training pairs clearly showed `output.shape != input.shape`.
Patterns like:

```python
result = [[bg]*W for _ in range(H)]   # H, W are INPUT dims
return result                          # never reshaped
```

The model had no "compute output shape first" prior.

**Phase 1 addresses this structurally:** every diff-size substrate
starts with a `SIZE H×W -> h×w` header (with relation tags), and 22.7%
of Phase 1.B training records target diff-size substrates. The model
literally cannot generate a diff-size substrate without committing to
output dimensions first.

**Phase 2 needs:**

1. Every shape-changing puzzle's `def solve()` target must begin with
   explicit output-shape computation, e.g.

   ```python
   def solve(input_grid):
       H, W = len(input_grid), len(input_grid[0])
       # output shape derived from train pairs; do not assume == input shape
       output_H, output_W = compute_output_shape(...)
       output = [[bg] * output_W for _ in range(output_H)]
   ```

2. Training records should bias toward shape-changing puzzles in
   the initial code-generation mix (above corpus-proportional 33%),
   to drive the "commit to output shape" prior even harder.

### 10.2 Missing imports (`from collections import …`)

**Finding:** ~10-20% of Run 1 code crashed at runtime because `Counter`,
`deque`, `defaultdict` were used without being imported. The model
"forgot" the import line on long-context prompts.

**Phase 2 fix:** standardize the first non-def lines of every code
target:

```python
def solve(input_grid):
    from collections import Counter, deque
    H, W = len(input_grid), len(input_grid[0])
    ...
```

Imports inside `solve()` rather than module-level so the SFT records
self-contain. Eliminates the 10–20% no-import crash mode.

### 10.3 Hardcoded background / palette values

**Finding:** Run 1 code occasionally hardcoded values like `bg = 8`
copied verbatim from a specific training pair's substrate. These fail
on new puzzles where the background is different.

**Phase 2 fix:** strip or rewrite hardcoded scalars in code training
data. Every `bg` / `border_color` / palette assignment must be
computed dynamically (e.g. `bg = Counter(c for row in grid for c in
row).most_common(1)[0][0]`).

The same principle goes back to Phase 1: our `substrate.background_of()`
is mechanical (frequency-based, tie by smallest color), and the
diff-size substrate's `BG <in_bg> -> <out_bg>` line trains the model
to think of background as a function of the grid, not a fixed digit.

### 10.4 Self-check before return

**Finding:** several Run 1 attempts returned `None`, returned
`input_grid` unchanged, or returned a 1D list because the output
construction had silently failed.

**Phase 2 fix:** training records should end every `solve()` with:

```python
    assert isinstance(output, list) and all(isinstance(r, list) for r in output)
    return output
```

Catches `None` / shape-mismatch return modes at the model's own output
boundary instead of in the validator.

### 10.5 Phase 3 corrector on near-misses

**Finding:** 7 Run 1 attempts achieved ≥90% cell-level accuracy but
failed exact-match — single off-by-one or boundary-case bugs that a
human reviewer could fix in minutes.

**Phase 3 design (Code Repair):** target these near-misses explicitly.
The system message is `Code Repair`. The user provides:

- the puzzle
- the wrong code
- validator feedback (which cells differed, what the expected values
  were)
- the diff map (`expected_cell - generated_cell` per location)

The assistant target is the corrected code. Training data is generated
from Run 1's near-miss artifacts plus synthetic corruptions of correct
code.

### 10.6 Overuse of "components + body/marker"

**Finding:** the model leans on connected-component detection as a
hammer, even for puzzles whose rule is geometric (rotation, reflection,
scaling).

**Phase 2 fix:** explicit format diversity in code targets — ensure
training data includes solvers using geometric primitives (transpose,
rotate, mirror, scale), tile-based primitives (repeat, tile), and
arithmetic primitives — not just BFS/DFS component finders.

### 10.7 Inference settings (informational)

Run 1 disconfirmed that lowering temperature helps. If anything, try
`temperature 1.0` with `pass@5` and aggregate at eval time. Not a
training change — relevant when launching the frozen-34 eval.

---

## 11. Open items (tracked here, not blocking)

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
