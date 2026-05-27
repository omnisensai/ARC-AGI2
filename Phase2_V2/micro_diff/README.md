# Diff-size micro corpus — the "different size" infer_T style

When OUTPUT dimensions ≠ INPUT, the same-size trick breaks: there is no per-cell
`.`/digit diff-map because there is no input cell under each output cell. So the
contract changes from *overwrite a copy of the input* to **construct a canvas,
then fill it**.

## The contract

```python
def solve(input_grid):
    T = infer_T(input_grid)        # (a) output geometry  + (b) how to fill it
    return apply_T(input_grid, T)  # build a fresh grid of T's shape, fill from T
```

`infer_T` must compute the **output shape from the input** (the geometry rule),
plus the **content**. `apply_T` constructs the output — it does NOT copy the
input. Two content styles cover almost everything:

- **Gather** (crop / tile / scale / reflect / transpose / extract):
  `output[r][c] = input[f(r,c)]`. T = output shape + a coordinate map. Pure
  rearrangement, no new colours. (`crop_to_bbox`, `scale_2x` here.)
- **Canvas + paint** (when genuinely new content): T = output shape + a base
  fill + `{(r,c): colour}` overrides; `apply_T` seeds the canvas and paints.
  Same "overwrite selected cells" idea as same-size, but on a constructed base.

The substrate philosophy is preserved: the model still *infers a transformation
and applies it mechanically* — it never draws the answer freehand. What's new
is that T carries geometry, and the geometry rule must be a function of the
input (crop-to-content, ×k scale, tile-by-count, extract-the-odd-one), learned
from the train pairs.

## Two things differ from same-size

1. **Prompt evidence**: diff-size T is lossy, so the SFT prompt shows
   `INPUT`, `OUTPUT`, and a `SIZE HxW -> hxw` fact per pair (not a per-cell T).
   `build_micro_sft.py --diff` does this; the system prompt is the diff-size one.
2. **Audit threshold**: small outputs are easier to transcribe, so the gate runs
   with a tighter literal cap: `build_micro.py --big-literal-max 8`.

The acceptance gate itself is unchanged and size-agnostic — it runs the solver
vs the OUTPUT on every pair, so it validates diff-size solvers as-is.

## Reference families (proven)

```
crop_to_bbox  60/60  (geometry from input content — the non-bg bbox)
scale_2x      60/60  (geometry by rule — x2 in each dimension)
```

Build/validate:
```
python Phase2_V2/micro/build_micro.py     <family> --dir micro_diff --big-literal-max 8 --n 60
python Phase2_V2/micro/build_micro_sft.py <family> --dir micro_diff --diff
```

## How this scales to the real corpus

The 343 real diff-size ARC tasks (Puzzle_Database, not yet built) use this same
contract. The agent swarm writes one canonical diff-size solver per task,
validated by the same gate with `--big-literal-max 8`. Curriculum-order by
geometry family: crop / extract / tile / scale / concat.
