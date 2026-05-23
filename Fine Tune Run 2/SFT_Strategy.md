# SFT Strategy — Fine Tune Run 2

The plan for the second supervised fine-tuning run, including the
two-phase curriculum, splits, hold-out discipline, substrate
specifications, and per-phase training-data format.

This document is the **strategy** layer. Parameters (mix ratios, LR,
seeds) are locked in the YAML configs alongside this file
(`phase1a_config.yaml`, `phase1b_config.yaml`, etc.). When this doc and
a config disagree, the config wins for execution and this doc gets
updated to match.

> **⚠ CURRENT STRUCTURE (supersedes the 4-stage prose below).** Phase 1
> is now a **5-stage** curriculum:
> `same_lit → diff_lit → same_rule → diff_rule → mixed`. The two T
> alphabets (pixel for same-size, facts for diff-size) are taught in
> isolation and reunite only in `mixed`. The **authoritative** stage
> list, system prompts, task mixes, and commands live in:
> - `phase1_prompts.py` + `PROMPTS.md` — the locked system prompts
>   (single source of truth; the verifier self-checks them)
> - `build_phase1_dataset.py` `STAGE_CONFIG` — filters + task mixes
> - `RUNBOOK.md` §1, §3 — the per-stage train/probe commands
>
> Sections §4, §7, §9 below still describe the earlier 4-stage framing
> (LIT/SAME/DIFF/MIXED) and are pending a prose reconciliation. Where
> they conflict with the files above, the files win.

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

Run 2 trains in three phases with three distinct goals:

| Phase | Goal | Targets |
|---|---|---|
| **Phase 1: Transformation grid literacy** | Teach the model to *see* the input→output transformation as a structured object (the "T grid"). No code generation. | T grids and output grids. |
| **Phase 2: Coding** | Teach the model to emit `def solve(input_grid)` Python that produces the correct output. | Python functions. |
| **Phase 3: Repair** | Teach the model to repair its own wrong code given validator feedback. | Corrected Python functions. |

Phase 1 itself is a four-stage curriculum (LIT → SAME → DIFF → MIXED).
LIT is pure substrate literacy across both alphabets; SAME/DIFF/MIXED
are substrate-type-split rule application. See §4.

The previous run (Run 1) hit 18% pass@1 / 24% pass@2 on a clean
held-out — with only **1 correct code per puzzle and 10 wrong** in the
training mix, and the "solve" task only 8% of the mix. That result
establishes the thesis: substrate-flavored SFT transfers. Run 2 builds
on it with:

1. A **curriculum** (Phase 1 → Phase 2 → Phase 3) instead of one mixed
   run, with Phase 1 itself split into three substrate-specific
   sub-stages.
2. **Strict held-outs** (34 A2E puzzles never touched) instead of the
   ad-hoc Run 1 splits.
3. **Disciplined task mix** in each stage.
4. A **per-pair substrate** (`encode_auto`) that handles diff-dimensions
   puzzles natively, not just same-dimensions.

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
| `a2e_dev_hard` | 30 | **Reserved for Phase 2/3 code-pipeline checkpoint selection.** Not touched during Phase 1. |
| `a2e_final_hard` | 34 | **Frozen.** Touched exactly once at the end of each run. No augmentation. |
| `a2e_leakers` | 6 | Excluded from hard-dev and final. May enter train **only** if the corresponding A1 version is also seen in train. |

`a2e_final_hard` is the headline number. If accidentally touched
(generation bug, eval leakage into train), regenerate from a fresh
random seed and re-roll all three A2E buckets. We are willing to lose
training data to keep the frozen 34 clean.

### 2.2 Train pool (~927 content-unique after holdouts)

Every other content-unique puzzle lives in the training pool: A1T +
A1E + A2T + the 6 A2E leakers, deduped by canonical content (~1027
total before holdout carves). The generator additionally holds out:

| Held-out | Count | Role |
|---|---|---|
| `phase1_probe` | 50 | Carved from train_pool. Between-Phase-1-sub-stage gate via `run_probe.py` exact-match scoring. Never gradient-updated. |
| `api_eval` | 50 | Carved from train_pool, distinct from `phase1_probe`. **Used for API-based inference testing across all phases** (Phase 1 substrate/grid runs, Phase 2 code-solver behavior, etc.). Locked as id list only — Phase 2's harness will render these into prompts when needed. Never gradient-updated. |

After both carves, the effective training pool is ~927 puzzles. Total
held-out across all stages: 34 + 30 + 50 + 50 = 164 / 1147 ≈ 14%.

### 2.3 Held-out usage discipline

Each held-out set has exactly one role. Crossing those roles
contaminates the metric.

| Set | When touched | How |
|---|---|---|
| `a2e_final_hard` | END of run, once | Loss + scoring on the LoRA adapter at the very end. No re-runs without seed change. |
| `a2e_dev_hard` | Phase 2/3 only | Code-pipeline checkpoint selection (in-flight or post-train). Not visible to Phase 1 at all. |
| `phase1_probe` | Between Phase 1 sub-stages (SAME / DIFF / MIXED) | Exact-match scoring per format via `run_probe.py`. Used to gate sub-stage progression. |
| `api_eval` | Anytime during development for API inference testing | Render puzzles fresh into whatever inference prompt format is being tested. |
| **In-flight loss monitor (val_set_size 0.02)** | Every `eval_steps` of Phase 1 training | Loss-only signal. **NOT a checkpoint-selection authority, NOT a generalization metric.** |

The in-flight loss carve is a 2% slice of the training set itself —
Axolotl's `val_set_size` default. It tells the operator whether loss
is converging; it does not gate stage progression. The only Phase 1
gate is `phase1_probe` exact-match scoring.

### 2.4 Hold-out unit

**Hold-outs are by augmentation parent, not by example.** Every
augmented variant of a held-out puzzle is held out. The split unit is
the (dedup-cluster, puzzle-id) pair: if puzzle `abc12345` is in
`a2e_final_hard`, then no D4 rotation, color permutation, or pair
subset of `abc12345` may appear anywhere in train.

The augmentation seed is per-puzzle so the held-out check is trivially
verifiable: "did this puzzle id appear in train under any
augmentation?" → grep the manifest.

### 2.5 Stratification

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
| `a2e_dev_hard` | n/a (not touched during Phase 1) | n/a | n/a |
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

### 4.1 Four-stage curriculum (literacy first, then substrate-split application)

Phase 1 trains four sequential LoRA checkpoints. The first stage is
pure literacy across both substrate alphabets; the next three split
rule application by substrate representation.

| Stage | LoRA name | Trains on | Continues from |
|---|---|---|---|
| **0-LIT** | `outputs/phase1_lit` | Single-pair literacy formats only (`pair_to_substrate`, `substrate_to_output`), both same and diff substrate types | Base Qwen-2.5-7B-Instruct |
| **1-SAME** | `outputs/phase1_same` | All formats; records filtered to same-dim T targets only | `phase1_lit` LoRA |
| **2-DIFF** | `outputs/phase1_diff` | All applicable formats; records filtered to diff-dim T targets only | `phase1_same` LoRA |
| **3-MIXED** | `outputs/phase1_mixed` | All formats; both same and diff records; full ARC puzzle framing in the system prompt | `phase1_diff` LoRA |

**Why LIT first.** Without a dedicated literacy stage, the model has
to learn the substrate alphabet *and* multi-pair rule application
simultaneously from step zero. When training fails we can't tell
whether it was alphabet confusion, format dispatch confusion, rule-
induction failure, or output-grid failure. The LIT stage isolates the
alphabet question:

> *Can the model speak the substrate alphabet before we ask it to
> reason with it?*

LIT trains only `pair_to_substrate` (encode-one-pair) and
`substrate_to_output` (decode-pixel-back). No multi-pair context, no
test prediction, no direct output. Short, focused, gated by the LIT
probe before we proceed to rule-application stages.

**Why split SAME / DIFF / MIXED by substrate type.** The same-dim and
diff-dim encodings are different alphabets:

- **Same-dim T grid:** per-cell, lossless. Cell-sovereign (`T[r,c]`
  depends only on `INPUT[r,c]` and `OUTPUT[r,c]`).
- **Diff-dim T text block:** aggregate, lossy, whole-grid statistics
  organized into fixed sections (`SIZE / BG / PALETTE / ROWS / COLS /
  BBOX`).

LIT teaches both alphabets in isolation; SAME / DIFF then layer
rule-application onto each alphabet separately; MIXED handles cross-
substrate dispatch.

### 4.2 Per-stage system prompts

Each stage uses its own system prompt. The model sees one prompt
during the training of that stage, and the prompt is what the eval
harness must use at inference for that adapter.

- **0-LIT prompt** covers both alphabets (same-dim grid + diff-dim
  aggregate). No ARC-puzzle multi-pair framing — LIT records are all
  single-pair. Same byte content as the DIFF prompt; the model is
  introduced to the full alphabet legend up front.

- **1-SAME prompt** narrows to only the same-dimensions alphabet. The
  model has already learned diff-dim from LIT (in its weights), but
  this stage's records are all same-dim and the prompt focuses
  attention there.

- **2-DIFF prompt** re-expands to both alphabets (same + diff). The
  records all target diff-dim, but acknowledging same-dim keeps the
  prior skill in active context.

- **3-MIXED prompt** adds the ARC-AGI puzzle framing: "exactly one
  transformation rule generalizes across all input/output pairs of a
  puzzle. The rule is encoded in T grids — one T per pair." This is
  the explicit invitation to perform rule transfer across pairs.

Exact byte content of all four prompts is the source of truth in
`build_phase1_dataset.py` (constants `SYSTEM_MESSAGE_LIT`,
`SYSTEM_MESSAGE_SAME`, `SYSTEM_MESSAGE_DIFF`, `SYSTEM_MESSAGE_MIXED`);
`SYSTEM_MESSAGE_LIT` is an alias for `SYSTEM_MESSAGE_DIFF` (identical
content). The verifier (`verify_records.py`) enforces them byte-for-
byte via `provenance.stage_key`.

Phase 2 and Phase 3 will use their own system messages (`Code Solver`,
`Code Repair`).

### 4.3 Phase 1 task formats

All five formats use the field-contract grammar (`INPUT:` / `OUTPUT:`
/ `T:`). The model sees only the field labels and the trailing-label
contract; internal format names below are bookkeeping for mix ratios
and per-task probe metrics.

| Internal label | User-prompt ends with | Target | Per-pair dispatch |
|---|---|---|---|
| `pair_to_substrate` | `T:` | T for the single pair shown | per pair via `encode_auto` |
| `substrate_to_output` | `OUTPUT:` | output grid (reconstructed from input + T) | **same-dim only** (no decoder for diff) |
| `multi_pair_to_rule` | `T:` | T for the trailing pair, given N-1 worked pairs | per pair via `encode_auto` |
| `test_substrate_prediction` | `T:` | T for the test pair, inferred from worked pairs | per pair via `encode_auto` |
| `direct_output_grid` | `OUTPUT:` | test output grid | n/a (output is the target) |

`substrate_to_output` requires the lossless same-dim T (because that
is the only T form with a deterministic decoder).

`multi_pair_to_rule` position rotation: for each augmented variant
with N train pairs, the generator emits N candidate items — one per
choice of trailing pair. The substrate-type filter applies per
candidate, so a stage only sees candidates whose trailing pair matches
its filter.

Format disambiguation by structure (no special labels needed):

- `pair_to_substrate`: one (INPUT, OUTPUT) shown, trailing `T:`.
- `substrate_to_output`: one (INPUT, T) shown, trailing `OUTPUT:`.
- `multi_pair_to_rule`: N-1 worked (INPUT, OUTPUT, T) triples + 1 pair
  with (INPUT, OUTPUT) but no T → trailing `T:`.
- `test_substrate_prediction`: N worked (INPUT, OUTPUT, T) triples +
  test pair with INPUT only → trailing `T:`.
- `direct_output_grid`: N (INPUT, OUTPUT) pairs + test INPUT only →
  trailing `OUTPUT:`.

### 4.4 Per-stage mix ratios

**0-LIT** (filter: both alphabets; single-pair literacy only):

| Format | Mix share |
|---|---|
| `pair_to_substrate` | 65% |
| `substrate_to_output` | 35% |

No multi-pair formats. No test prediction. No direct output. The
substrate_to_output records are intrinsically same-dim (only alphabet
with a decoder); pair_to_substrate covers both same and diff.

**1-SAME** (filter: only candidates whose target T is a same-dim grid):

| Format | Mix share |
|---|---|
| `pair_to_substrate` | 15% |
| `substrate_to_output` | 15% |
| `multi_pair_to_rule` | 25% |
| `test_substrate_prediction` | 35% |
| `direct_output_grid` | 10% |

**1-DIFF** (filter: only candidates whose target T is a diff-dim text
block). `substrate_to_output` is absent because the diff-dim T has no
decoder:

| Format | Mix share |
|---|---|
| `pair_to_substrate` | 20% |
| `multi_pair_to_rule` | 30% |
| `test_substrate_prediction` | 40% |
| `direct_output_grid` | 10% |

**1-MIXED** (no filter — both same and diff candidates):

| Format | Mix share |
|---|---|
| `pair_to_substrate` | 5% |
| `substrate_to_output` | 5% |
| `multi_pair_to_rule` | 25% |
| `test_substrate_prediction` | 40% |
| `direct_output_grid` | 25% |

`direct_output_grid` is weighted up in 1-MIXED because diff-dim pairs
can no longer ride on `substrate_to_output` to learn the input→output
relationship; raw-output prediction picks up that slack.

### 4.5 Per-stage probes

Each stage's probe (`phase1_<stage>_probe.jsonl`) is identity-augmented
records from the 50 held-out probe puzzles, filtered to the stage's
substrate type. Probes are evaluated with greedy decode and exact-match
scoring.

**0-LIT done signal:**

| Probe | Threshold |
|---|---|
| `pair_to_substrate` exact (same-dim) | ≥ 95% |
| `pair_to_substrate` exact (diff-dim) | ≥ 90% (section accuracy) |
| `substrate_to_output` exact (same-dim only) | ≥ 95% |

If LIT clears these thresholds, the model can read/write the
substrate alphabets cleanly and we have a solid foundation for rule-
application stages. If it doesn't, extend LIT before moving on —
catching alphabet confusion here is much cheaper than fighting it
inside SAME/DIFF/MIXED.

**1-SAME done signal:**

| Probe | Threshold |
|---|---|
| `pair_to_substrate` exact (same-dim) | ≥ 95% |
| `substrate_to_output` exact | ≥ 95% |
| `multi_pair_to_rule` exact (same-dim) | ≥ 90% |
| `test_substrate_prediction` exact (same-dim) | meaningfully above baseline |

**1-DIFF done signal:**

| Probe | Threshold |
|---|---|
| `pair_to_substrate` exact (diff-dim) | ≥ 90% |
| `multi_pair_to_rule` exact (diff-dim) | ≥ 85% |
| `test_substrate_prediction` exact (diff-dim) | meaningfully above baseline |
| Forgetting check: same-dim probe metrics from 1-SAME | within 5pp of 1-SAME |

**1-MIXED done signal:**

| Probe | Threshold |
|---|---|
| All same-dim probe metrics | within 5pp of 1-SAME (no forgetting) |
| All diff-dim probe metrics | within 5pp of 1-DIFF (no forgetting) |
| `test_substrate_prediction` and `direct_output_grid` combined accuracy | exceeds either single-stage baseline |

If any threshold misses, the responsible stage gets extended before
moving on. Same-dim and diff-dim metrics are always reported
separately so degradation is localized to the right substrate type.

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

### 7.2 The three Phase 1 system messages

Phase 1 uses **three distinct system messages**, one per sub-stage
(SAME / DIFF / MIXED). Each is a compact English-prose legend that
defines the substrate alphabet appropriate to that stage. Putting the
legend in the system prompt leverages Qwen's pretraining instead of
forcing the model to learn the symbols by gradient descent.

Each stage's records carry only that stage's system message. The
byte-level source of truth is `build_phase1_dataset.py` (constants
`SYSTEM_MESSAGE_SAME`, `SYSTEM_MESSAGE_DIFF`, `SYSTEM_MESSAGE_MIXED`);
`verify_records.py` enforces them per-record via `provenance.stage_key`.

**SAME prompt (~85 tokens):** only the same-dimensions alphabet.

```
Encode the transformation from INPUT to OUTPUT as a T grid. Each cell
is an atomic unit colored 0-9.

T grid legend when INPUT and OUTPUT have the same dimensions
(e.g. 3x3 -> 3x3):
  .       cell unchanged
  0-9     cell changed to this output color
Each cell is independent: T[r,c] depends only on INPUT[r,c] and
OUTPUT[r,c], not on neighbors. Lossless — OUTPUT is fully
reconstructible from INPUT + T.
```

**DIFF prompt (~210 tokens):** same opener plus a diff-dimensions
section and the relation-tag table. The SAME prompt's body is
preserved so the model retains its same-dim skill while learning diff.

```
[SAME body unchanged]

T grid legend when INPUT and OUTPUT have different dimensions
(e.g. 3x3 -> 2x4):
T is an aggregate text block with these sections in fixed order,
separated by blank lines:
  SIZE     overall dimensions:  H x W -> h x w  with relation tags
  BG       background color:  in_bg -> out_bg  with relation tag
  PALETTE  per-color count change
  ROWS     per-row dominant colors + non-bg counts (INPUT and OUTPUT)
  COLS     per-column dominant colors + non-bg counts (INPUT and OUTPUT)
  BBOX     per-color bounding box (INPUT and OUTPUT)
Whole-grid statistics — diagnostic only, not lossless. No per-cell
decoder.

Relation tags for numeric pairs a -> b:
  =        a == b
  ×N       b = a * N, integer N > 1
  ÷N       a = b * N, integer N > 1
  Δ±N      additive offset (b - a)
  new      a == 0 and b > 0
  dropped  a > 0 and b == 0
```

**MIXED prompt (~250 tokens):** replaces the opening with the ARC-AGI
puzzle framing — "exactly one transformation rule generalizes across
all input/output pairs of a puzzle." This is the explicit invitation
to perform rule transfer in `multi_pair_to_rule` and
`test_substrate_prediction`. Body (both alphabets + relation tags) is
identical to DIFF.

```
ARC-AGI puzzle contains INPUT/OUTPUT grid pairs where each cell is an
atomic unit colored 0-9. There is exactly one transformation rule that
generalizes across all input/output pairs of a puzzle. The rule is
encoded in T grids — one T per pair, and the underlying rule is the
same across all of them.

[same body as DIFF]
```

With `train_on_inputs: false` the system tokens contribute zero loss
— pure context. The progression (SAME → DIFF → MIXED) is the legend
growing in lockstep with the model's expanding capability.

Phase 2 will use its own system messages (`Code Solver` for codegen,
`Code Repair` for repair). One system message per phase-stage.

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

The dataset generator writes (per stage in {`lit`, `same`, `diff`, `mixed`}):

```
Fine Tune Run 2/data_sft/phase1_<stage>_train.jsonl.gz
Fine Tune Run 2/data_sft/phase1_<stage>_probe.jsonl
Fine Tune Run 2/data_sft/phase1_<stage>_manifest.json
```

There is **no `phase1_<stage>_dev.jsonl`** — Phase 1 uses Axolotl's
`val_set_size: 0.02` for in-flight loss monitoring (a 2% carve from
the train set). The 30 `a2e_dev_hard` puzzles are reserved for Phase
2/3 and are not rendered in Phase 1.

Plus the locked split files (shared across stages):

```
Fine Tune Run 2/splits/phase1_splits.json
Fine Tune Run 2/splits/frozen_final_eval_ids.txt   (34 puzzle ids)
Fine Tune Run 2/splits/phase1_probe_ids.txt         (50 puzzle ids)
Fine Tune Run 2/splits/api_eval_ids.txt             (50 puzzle ids)
```

The frozen 34 puzzles live physically isolated in
`Fine Tune Run 2/puzzles_frozen/` and are never read by the generator.

---

## 8. Files

| Path | Purpose |
|---|---|
| `Fine Tune Run 2/SFT_Strategy.md` | this document |
| `Fine Tune Run 2/phase1_lit_axolotl.yaml` | trainer config for LIT stage (from base Qwen) |
| `Fine Tune Run 2/phase1_same_axolotl.yaml` | trainer config for SAME stage (continues LIT LoRA) |
| `Fine Tune Run 2/phase1_diff_axolotl.yaml` | trainer config for DIFF stage (continues SAME LoRA) |
| `Fine Tune Run 2/phase1_mixed_axolotl.yaml` | trainer config for MIXED stage (continues DIFF LoRA) |
| `Fine Tune Run 2/build_phase1_dataset.py` | dataset generator (per-stage substrate filter) |
| `Fine Tune Run 2/build_splits.py` | split + isolate the 34 frozen puzzles |
| `Fine Tune Run 2/verify_records.py` | byte-level invariant checker for all stages |
| `Fine Tune Run 2/run_probe.py` | per-format exact-match probe harness |
| `Fine Tune Run 2/classify_origin.py` | content-unique origin classifier |
| `Fine Tune Run 2/verify_augmentations.py` | D4 + color + subset rule-preservation checks |
| `Fine Tune Run 2/puzzles/` | input corpus (1886 files after frozen 34 isolated) |
| `Fine Tune Run 2/puzzles_frozen/` | locked 34 final-eval puzzles, isolated from generator |
| `Fine Tune Run 2/puzzles/README.md` | puzzle fact sheet |
| `Fine Tune Run 2/data_sft/` | generated SFT training data (3 stages × train/probe/manifest) |
| `Fine Tune Run 2/splits/` | locked puzzle id lists: phase1_probe, api_eval, frozen_final_eval, full splits manifest |
| `substrate.py` | substrate library (top of repo, shared) |
| `scripts/test_diffsize_substrate.py` | substrate regression test |

---

## 9. Execution — LoRA chaining across stages and phases

Run 2 default execution: **one LoRA adapter, continued across all
stages and all phases.** No merge between Phase 1 and Phase 2.

This is "Path α" — chosen for simplicity, easier attribution, single
adapter at every checkpoint, and Run 1 evidence that one LoRA can
absorb the substrate + code skill stack (Run 1 hit 18% pass@1 with
exactly this approach, just without the curriculum staging).

The trade is forgetting risk: each phase's training can overwrite
prior weights. We mitigate with:

- 5–10% carry of the prior phase's task formats in the next phase's
  mix (already built into the Phase 1 stage mixes).
- Lower learning rate at Phase 2 if forgetting shows up after the
  first run.
- Re-running prior-phase probes after each phase to detect drift.

Path β (merge between phases) is documented in §9.3 as an option to
revisit if Path α produces unacceptable forgetting on Phase 1 probes
after Phase 2 training. Until then, Path α is the default.

### 9.1 Phase 1 chain (one adapter, four sub-stages)

```
Base Qwen2.5-7B-Instruct
  ↓ axolotl train phase1_lit_axolotl.yaml
outputs/phase1_lit/          LoRA after LIT stage (literacy)
  ↓ axolotl train phase1_same_axolotl.yaml
  ↑ lora_model_dir: outputs/phase1_lit
outputs/phase1_same/         same adapter, after SAME stage
  ↓ axolotl train phase1_diff_axolotl.yaml
  ↑ lora_model_dir: outputs/phase1_same
outputs/phase1_diff/         same adapter, after DIFF stage
  ↓ axolotl train phase1_mixed_axolotl.yaml
  ↑ lora_model_dir: outputs/phase1_diff
outputs/phase1_mixed/        same adapter, fully trained Phase 1
```

All four sub-stages (LIT, SAME, DIFF, MIXED) share the same LoRA
shape and target modules. The model knowledge accumulates within one
adapter; the LoRA never gets reset across sub-stages.

System prompt progression:
- LIT: legend covering both alphabets, no puzzle framing
- SAME: legend narrowed to same-dim only
- DIFF: legend re-expanded to both alphabets (preserves same-dim)
- MIXED: full legend + ARC puzzle framing (sets up rule transfer)

Probe between each sub-stage via `phase1_<stage>_probe.jsonl`. If a
stage misses its done-signal thresholds, extend it before moving on.
Cross-stage forgetting is monitored by re-running the prior stage's
probe after the next stage trains.

### 9.2 Phase 1 → Phase 2 → Phase 3 chain (Path α — chosen default)

```
outputs/phase1_mixed/    final Phase 1 LoRA
  ↓ axolotl train phase2_axolotl.yaml
  ↑ lora_model_dir: outputs/phase1_mixed
outputs/phase2_code/     same adapter, now also trained on code
  ↓ axolotl train phase3_axolotl.yaml
  ↑ lora_model_dir: outputs/phase2_code
outputs/phase3_repair/   same adapter, now also trained on repair
```

One LoRA adapter end to end. Test at every checkpoint via
`base + this_adapter`. Each phase's config carries 5–10% of the prior
phase's task formats to prevent forgetting.

### 9.3 Path β (merge between phases) — fallback, not default

If Path α shows forgetting (Phase 1 probes degrade after Phase 2
training beyond the 5pp tolerance), switch to Path β: merge the Phase
1 LoRA into the base, train a fresh Phase 2 LoRA on the merged
checkpoint. Same pattern between Phase 2 and Phase 3.

```
Base Qwen
  ↓ Phase 1 SAME + DIFF + MIXED (LoRA continues, no merge)
outputs/phase1_mixed/                 LoRA adapter (final Phase 1)
  ↓ merge into base weights
outputs/phase1_merged/                full 7B model, ~15GB bf16
  ↓ Phase 2 trains FRESH LoRA on phase1_merged
outputs/phase2_code_solver/           new Phase 2 adapter
  ↓ merge
outputs/phase2_merged/                full 7B model
  ↓ Phase 3 trains FRESH LoRA on phase2_merged
outputs/phase3_code_repair/           new Phase 3 adapter
```

Disk cost: each merged checkpoint is the full model (~15GB bf16). Path
β decision happens at the Phase 1 → Phase 2 boundary; not blocking
Phase 1.

### 9.3 Naming convention

| Output dir | What it is |
|---|---|
| `outputs/phase1_lit/` | LoRA adapter after LIT stage (from base Qwen) |
| `outputs/phase1_same/` | same adapter, after SAME stage (continues `phase1_lit`) |
| `outputs/phase1_diff/` | same adapter, after DIFF stage (continues `phase1_same`) |
| `outputs/phase1_mixed/` | same adapter, fully trained Phase 1 (continues `phase1_diff`) |
| `outputs/phase2_code/` | **Path α default**: same adapter, now also trained on Phase 2 code data (continues `phase1_mixed`) |
| `outputs/phase3_repair/` | **Path α default**: same adapter, now also trained on Phase 3 repair data (continues `phase2_code`) |
| `outputs/phase1_merged/` | Path β fallback: base + Phase 1 LoRA merged into one full model |
| `outputs/phase2_merged/` | Path β fallback |
| `outputs/phase3_merged/` | Path β fallback |

### 9.4 What "merge" means operationally (Path β only)

If we ever invoke Path β:

1. Load base (or previous merged) model.
2. Attach the most recent LoRA adapter via `peft.PeftModel.from_pretrained`.
3. Call `model = model.merge_and_unload()`.
4. Save: `model.save_pretrained(out_dir)` + tokenizer.

A short script will live at `Fine Tune Run 2/merge_lora.py` when first
needed. Not built yet (Path α is the default).

### 9.5 Decision points

- **After 0-LIT:** Run probe on `phase1_lit_probe.jsonl`. If literacy
  thresholds pass (≥95% same-dim pair, ≥90% diff-dim section, ≥95%
  substrate_to_output), proceed to 1-SAME. If not, extend LIT —
  catching alphabet confusion here is much cheaper than fighting it
  in later stages.
- **After 1-SAME:** Run probe on `phase1_same_probe.jsonl`. If
  thresholds pass, proceed to 1-DIFF. If not, extend 1-SAME.
- **After 1-DIFF:** Run probe on `phase1_diff_probe.jsonl` + forgetting
  check via `phase1_same_probe.jsonl`. If diff thresholds pass AND
  same-dim metrics stay within 5pp of post-SAME baseline, proceed to
  1-MIXED.
- **After 1-MIXED:** Run probes on all three (same, diff, mixed).
  Optionally run API-eval inference on `api_eval` puzzles to sanity-
  check end-to-end behavior. If no degradation and mixed metrics
  exceed single-stage baselines, Phase 1 is done. **Continue same
  LoRA into Phase 2** (Path α).
- **After Phase 2:** Re-run Phase 1 probes against the Phase 2 adapter.
  If forgetting > 5pp on any Phase 1 metric, switch to Path β for
  Phase 3 (or for a re-do of Phase 2).
- **Phase 2/3 details** are out of scope for this document; see §10
  for the Run 1 lessons that drive Phase 2 design.

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
