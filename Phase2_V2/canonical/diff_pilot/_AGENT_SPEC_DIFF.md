# Canonical diff-size solver — agent brief

You are generating ONE verified canonical ARC solver for a distillation corpus.
This is a **DIFF-SIZE** puzzle: the OUTPUT dimensions differ from the INPUT.
You may use ALL pairs (train AND test) as evidence — the goal is the best
canonical solver, not Kaggle inference.

Your task message gives the puzzle id and its pairs as `list[list[int]]` grids,
colors 0-9 (already parsed from the database's flat token format for you).

## The diff-size contract

The same-size per-cell `.`/digit diff-map does NOT apply: there is no input cell
under each output cell. So you **construct** the output instead of overwriting a
copy of the input:

    def solve(input_grid):
        T = infer_T(input_grid)        # (a) output geometry (h,w) + (b) how to fill it
        return apply_T(input_grid, T)  # build a fresh h x w grid, fill from T

`infer_T` computes the output SHAPE **as a function of the input** (the geometry
rule — crop to content, x k scale, tile, extract a region) plus the content
rule. `apply_T` builds the new grid. Two content styles cover almost everything:

- **Gather**: `output[r][c] = input[f(r,c)]` — crop / tile / scale / reflect /
  transpose / extract. T = output shape + a coordinate map. No new colors.
- **Canvas + paint**: T = output shape + a base fill + `{(r,c): color}` paints,
  for genuinely new content. `apply_T` seeds the canvas and paints.

## CRITICAL convention: background is 0, NOT most-common

ARC's background is the structural **0**. Do NOT use `Counter(...).most_common`
to guess the background — recoloring augmentations and dense foregrounds make
another color the majority and silently break the rule. Default to `bg = 0`
unless a task clearly frames on a different constant. (This single mistake
failed two of the three pilot solvers until fixed.)

## Hard rules (AST-audited; rejected otherwise)

- Must contain the `infer_T`/`apply_T` decomposition. Geometry must be inferred,
  not a constant output shape unrelated to the input.
- NO hardcoded output grid, NO `if input == [...]`, NO fingerprint/lookup.
- Literal cap is TIGHT for diff-size (small outputs are easy to transcribe):
  no list-of-lists literal of total size >= 8. Build the output with loops.
- Standard library only.

## Validated exemplars (all 6/6 across augmentation variants)

Self-tiling fractal (3x3 -> 9x9): block (R,C) stamps the whole grid iff on.
```python
def infer_T(g):
    H, W = len(g), len(g[0]); return {"h": H * H, "w": W * W}
def apply_T(g, T):
    H, W = len(g), len(g[0]); out = [[0] * (W * W) for _ in range(H * H)]
    for R in range(H):
        for C in range(W):
            if g[R][C] != 0:
                for r in range(H):
                    for c in range(W):
                        out[R * H + r][C * W + c] = g[r][c]
    return out
def solve(input_grid):
    return apply_T(input_grid, infer_T(input_grid))
```

Split + compare (3x7 -> 3x3): divider column splits two halves; mark 2 where
both halves are non-zero (a gather of geometry + paint of the AND).
```python
def infer_T(g):
    H, W = len(g), len(g[0])
    sep = next(c for c in range(W)
               if len({g[r][c] for r in range(H)}) == 1 and g[0][c] != 0)
    return {"sep": sep, "h": H, "w": sep}
def apply_T(g, T):
    sep = T["sep"]; left = [r[:sep] for r in g]; right = [r[sep + 1:] for r in g]
    h, w = len(left), len(left[0]); out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if left[r][c] != 0 and right[r][c] != 0:
                out[r][c] = 2
    return out
def solve(input_grid):
    return apply_T(input_grid, infer_T(input_grid))
```
(Tiling-with-mirror `00576224` is a third validated exemplar — see
`solvers/00576224.py`.)

## Process (verify — do not trust yourself)

1. Study ALL pairs. Establish the SIZE relation first (h,w as a function of
   H,W or of the input content), then the content rule.
2. Write `solve()` in `infer_T`/`apply_T` form, `bg = 0`.
3. Test harness in `/tmp`: run `solve(input)` for every pair, compare exactly,
   print PASS/FAIL. Run it. Fix `infer_T` and iterate until ALL pass.
4. Write the final solver (no harness) to the solvers dir. The orchestrator
   re-runs it through the canonical gate (`accept(..., big_literal_max=8)`)
   independently — faking success or hardcoding is caught.

## Report back (concise)

ALL-PASS or not, iterations, the geometry rule + content rule, final `solve()`.
If you cannot pass all pairs honestly, say so and list which pairs fail and why.
