# Phase 1 Prompts — Source of Truth

This document holds the **exact, locked system prompts** for every Phase 1
stage. It is the canonical reference. When the dataset is (re)built, the
generator must use these prompts **verbatim** — do not paraphrase, re-derive,
or "approximately" reconstruct them mid-run.

Implementation contract (to be wired once all stages are locked):
- The exact bytes live in a single machine-read file (`phase1_prompts.py`).
- `build_phase1_dataset.py` imports prompts from it (no copy).
- `verify_records.py` imports the same ones (no copy).
- A consistency check asserts the prompts in THIS doc match that file, so the
  human doc and the code can never silently diverge.

Prompts are assembled from reusable blocks so a legend is defined once:
- `LEGEND_PIXEL` — same-size T (per-cell pixel grid)
- `LEGEND_FACTS` — diff-size T (aggregate facts block)
- each stage prompt = stage-specific header + the relevant legend(s)

---

## Curriculum (5 focused stages)

The two T-alphabets (pixel vs facts) are taught in isolation and only reunite
in the final MIXED stage. Same-size pairs always encode to pixel-T; diff-size
pairs always encode to facts-T — deterministic, per pair, enforced by the
substrate library.

| Order | Stage | Pairs | Size | Legend in prompt | Tasks |
|---|---|---|---|---|---|
| 1 | same-literacy | 1 | same | pixel only | `pair_to_substrate`, `substrate_to_output` |
| 2 | diff-literacy | 1 | diff | facts only | `pair_to_substrate` (no decoder → no `substrate_to_output`) |
| 3 | same-rule | many | same | pixel only | multi_pair, test_prediction, direct_output |
| 4 | diff-rule | many | diff | facts only | multi_pair, test_prediction, direct_output |
| 5 | mixed | many | both | pixel + facts + puzzle framing | all |

Field-contract reminder: user prompts use only the structural labels
`INPUT:` / `OUTPUT:` / `T:`, one blank line between blocks, and end on the
trailing label whose value the model must produce (no prose instructions in
the label slot).

---

## Stage 1 — same-literacy  *(LOCKED)*

**Teaches:** one same-size pair → write the pixel-T that records the change.
The model's first lesson: see the exact before→after difference, one pair, no
neighbors, no rule generalization.

**System prompt:**

```
Transformation dynamics:
T encodes how the INPUT grid becomes the OUTPUT grid.

When INPUT and OUTPUT share [r,c] dimensions, T is per-cell and lossless — OUTPUT can be rebuilt exactly from INPUT via T.

T encoding (per cell [r,c]):
  .       INPUT -> OUTPUT cell unchanged
  0-9     INPUT -> OUTPUT cell changed to this color
```

**User prompt shape** (`pair_to_substrate`):
```
INPUT:
<grid>

OUTPUT:
<grid>

T:
```
**User prompt shape** (`substrate_to_output`):
```
INPUT:
<grid>

T:
<pixel grid>

OUTPUT:
```

---

## Stage 2 — diff-literacy  *(LOCKED)*

**Teaches:** one diff-size pair → write the aggregate facts-T. The contrast
with Stage 1 is the lesson: mismatched dims have no cell correspondence, so T
is a whole-grid summary, lossy, NOT reversible. Only `pair_to_substrate` here
— diff-size T has no decoder, so `substrate_to_output` cannot exist for it.

Shares lines 1–2 verbatim with Stage 1 (one frame); diverges at the dimension
test. Section names (SIZE/BG/PALETTE/ROWS/COLS/BBOX) and relation tags
(= ×N ÷N Δ±N new dropped) are mechanical — must match `diffsize_encode`
output byte-for-byte; do not reword them.

**System prompt:**

```
Transformation dynamics:
T encodes how the INPUT grid becomes the OUTPUT grid.

When INPUT and OUTPUT [r,c] dimensions mismatch, T is aggregate and lossy — OUTPUT cannot be rebuilt exactly from INPUT via T.

T encoding (aggregate summary):
  SIZE     H x W -> h x w   with relation tags
  BG       in_bg -> out_bg   with relation tag
  PALETTE  per-color count change
  ROWS     per-row dominant colors + non-bg counts (INPUT and OUTPUT)
  COLS     per-column dominant colors + non-bg counts (INPUT and OUTPUT)
  BBOX     per-color bounding box (INPUT and OUTPUT)

Relation tags for a -> b:
  =        a == b
  ×N       b = a*N (N>1)
  ÷N       a = b*N (N>1)
  Δ±N      additive offset b - a
  new      a == 0, b > 0
  dropped  a > 0, b == 0
```

**User prompt shape** (`pair_to_substrate`):
```
INPUT:
<grid>

OUTPUT:
<grid>

T:
```

## Stage 3 — same-rule  *(LOCKED)*

**Teaches:** multi-pair, same-size. First stage where multiple pairs appear.
Tasks: `multi_pair_to_rule` (produce trailing pair's T), `test_substrate_prediction`
(infer the transformation from worked pairs, apply to a hidden test pair),
`direct_output_grid` (predict the test output directly). The
"transformation generalizes across pairs" line is what makes the worked pairs
relevant to the hidden test pair — `test_substrate_prediction` depends on it.

Same pixel legend as Stage 1 (same-size). Shares lines 1–2 verbatim with
Stages 1–2; line 3 introduces multi-pair generalization and is **identical to
Stage 4's line 3** (the two rule stages share one framing; they differ only in
same-size vs diff-size legend). NOTE: there is one shared rule across pairs;
each T encodes it for its own pair, so the T's differ pair-to-pair (T1 ≠ T2).

**System prompt:**

```
Transformation dynamics:
T encodes how the INPUT grid becomes the OUTPUT grid.
Each T encodes exactly one transformation rule that applies across all pairs.

When INPUT and OUTPUT share [r,c] dimensions, T is per-cell and lossless — OUTPUT can be rebuilt exactly from INPUT via T.

T encoding (per cell [r,c]):
  .       INPUT -> OUTPUT cell unchanged
  0-9     INPUT -> OUTPUT cell changed to this color
```

## Stage 4 — diff-rule  *(LOCKED)*

**Teaches:** multi-pair, diff-size. Same tasks as Stage 3 but for diff-size
pairs (no `substrate_to_output` — facts-T has no decoder). Line 3 is identical
to Stage 3; the facts legend is identical to Stage 2. Section names and
relation tags are mechanical — must match `diffsize_encode` byte-for-byte.

**System prompt:**

```
Transformation dynamics:
T encodes how the INPUT grid becomes the OUTPUT grid.
Each T encodes exactly one transformation rule that applies across all pairs.

When INPUT and OUTPUT [r,c] dimensions mismatch, T is aggregate and lossy — OUTPUT cannot be rebuilt exactly from INPUT via T.

T encoding (aggregate summary):
  SIZE     H x W -> h x w   with relation tags
  BG       in_bg -> out_bg   with relation tag
  PALETTE  per-color count change
  ROWS     per-row dominant colors + non-bg counts (INPUT and OUTPUT)
  COLS     per-column dominant colors + non-bg counts (INPUT and OUTPUT)
  BBOX     per-color bounding box (INPUT and OUTPUT)

Relation tags for a -> b:
  =        a == b
  ×N       b = a*N (N>1)
  ÷N       a = b*N (N>1)
  Δ±N      additive offset b - a
  new      a == 0, b > 0
  dropped  a > 0, b == 0
```

## Stage 5 — mixed  *(LOCKED)*

**Teaches:** everything — multi-pair, both sizes, all tasks. This is the
final adapter shipped for eval, so its prompt must stand alone: the model has
no focused stage to lean on at inference, so BOTH legends are present and the
dimension test selects which applies. Combines the shared opening + the
unified rule line + Stage 1's pixel branch + Stage 2's facts branch.

**System prompt:**

```
Transformation dynamics:
T encodes how the INPUT grid becomes the OUTPUT grid.
Each T encodes exactly one transformation rule that applies across all pairs.

When INPUT and OUTPUT share [r,c] dimensions, T is per-cell and lossless — OUTPUT can be rebuilt exactly from INPUT via T.

T encoding (per cell [r,c]):
  .       INPUT -> OUTPUT cell unchanged
  0-9     INPUT -> OUTPUT cell changed to this color

When INPUT and OUTPUT [r,c] dimensions mismatch, T is aggregate and lossy — OUTPUT cannot be rebuilt exactly from INPUT via T.

T encoding (aggregate summary):
  SIZE     H x W -> h x w   with relation tags
  BG       in_bg -> out_bg   with relation tag
  PALETTE  per-color count change
  ROWS     per-row dominant colors + non-bg counts (INPUT and OUTPUT)
  COLS     per-column dominant colors + non-bg counts (INPUT and OUTPUT)
  BBOX     per-color bounding box (INPUT and OUTPUT)

Relation tags for a -> b:
  =        a == b
  ×N       b = a*N (N>1)
  ÷N       a = b*N (N>1)
  Δ±N      additive offset b - a
  new      a == 0, b > 0
  dropped  a > 0, b == 0
```

---

## Status: all 5 stage prompts LOCKED

Next implementation step (not yet done): create the single machine-read
source file (`phase1_prompts.py`) holding these exact bytes, wire
`build_phase1_dataset.py` and `verify_records.py` to import from it, and add a
check asserting this doc matches that file. Until then, these blocks are the
authority.

---

# Phase 2 — code-solver  *(LOCKED)*

**Teaches:** given the visible training pairs as INPUT+T evidence, write one
Python `def solve(input_grid):` that implements the single rule shared by all
pairs. This is a different target from Phase 1 (executable code, not a T or an
output grid). Continues the substrate chain from the `same_rule` adapter.

**Canonical source:** the exact bytes live inline as `SYSTEM` in
`scripts/build_phase2_code_dataset.py`. This block must match it verbatim.

**System prompt:**

```
Code Solver.
You are given ARC training pairs. For each pair, T marks what changed from INPUT to OUTPUT (same-size: per-cell, '.'=unchanged, 0-9=new color; diff-size: an aggregate facts block). T is evidence of the rule, not the answer.
Write one Python function `def solve(input_grid):` that implements the single rule shared by all pairs and returns the OUTPUT for any input of this puzzle.
Return ONLY Python. Exactly one function `solve(input_grid)`. Return a non-empty rectangular list[list[int]] with cells 0-9. Deterministic; no I/O, no prints, no imports beyond math, collections, itertools, functools, copy, operator, statistics, heapq, bisect, re. If the output shape differs from the input, compute the output dimensions first and allocate a new grid; do not start from a copy.
```

**User prompt shape** — same-size puzzles use the compact INPUT+T encoding
(OUTPUT is recoverable from INPUT+T, so it is dropped to save ~1/3 of tokens);
diff-size puzzles keep the OUTPUT block (facts-T is lossy). Every user message
ends on the trailing `Write def solve(input_grid):` cue.

Compact (same-size), one or more pairs:
```
INPUT:
<grid>

T:
<pixel grid>

INPUT:
<grid>

T:
<pixel grid>

Write def solve(input_grid):
```

`pseudo_test` variant — appends a bare test input (no OUTPUT, no T) after the
demonstration pairs, matching the competition inference shape:
```
INPUT:
<grid>

T:
<pixel grid>

TEST INPUT:
<grid>

Write def solve(input_grid):
```

**Assistant target:** the `solve()` function only.
```
def solve(input_grid):
    ...
    return out
```

**Three user-message variants** (system prompt + assistant target identical
across all three; only the demonstrated pairs differ):

| Variant | Mix | User message shows |
|---|---|---|
| `all_pairs` | 35% | every known pair as INPUT+T |
| `subset_cycled` | 40% | a rotating subset of pairs |
| `pseudo_test` | 25% | some pairs with T, then a bare `TEST INPUT:` (no T) |

**Training/masking contract:** `type: chat_template`,
`chat_template: tokenizer_default` (the model's own Qwen template),
`train_on_inputs: false` — loss is computed **only on the assistant turn** (the
`solve()` code plus the trailing `<|im_end|>` stop token). System + user are
masked context. Records whose estimated token length exceeds the 8192 window
are dropped at build time so trainer truncation can never eat the code target
or its stop token.
