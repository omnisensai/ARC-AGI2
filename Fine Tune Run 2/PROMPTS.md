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
Stages 1–2; line 3 introduces multi-pair generalization. NOTE the subject of
"generalizes" is the transformation (encoded in T), NOT T itself — T is
per-pair and differs across pairs (T1 ≠ T2); the transformation behind them is
what is shared.

**System prompt:**

```
Transformation dynamics:
T encodes how the INPUT grid becomes the OUTPUT grid.
The same transformation dynamic encoded in T generalizes across pairs.

When INPUT and OUTPUT share [r,c] dimensions, T is per-cell and lossless — OUTPUT can be rebuilt exactly from INPUT via T.

T encoding (per cell [r,c]):
  .       INPUT -> OUTPUT cell unchanged
  0-9     INPUT -> OUTPUT cell changed to this color
```

## Stage 4 — diff-rule  *(PENDING)*

## Stage 5 — mixed  *(PENDING)*
