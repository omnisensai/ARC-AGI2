# Diff-size canonical grammar — for external review

## The problem

ARC puzzles split into two cases:
- **Same-size** — output dimensions equal input dimensions. Cell-by-cell diff is well-defined.
- **Diff-size** — output dimensions differ from input (~364 of ~1147 puzzles). Cell-by-cell diff is undefined: there is no input cell at output coordinate (r,c) when the grids have different shapes.

For training a code-generating LoRA, we wanted **one solver grammar across the entire corpus** so the model learns a single, consistent function shape regardless of the operation. The challenge: how do we extend our canonical same-size grammar to diff-size without breaking that uniformity?

## Same-size grammar (locked, already proven)

```python
def solve(input_grid):
    T = infer_T(input_grid)            # T: dict[(r,c) -> new_value]
    return apply_T(input_grid, T)      # copy input + overwrite cells in T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out
```

- **`T` semantics**: which cells change and to what. Cells absent from T stay unchanged. Lossless representation of input → output.
- **SFT prompt evidence**: each train pair is shown as `(INPUT grid, per-cell T)` where `.` = unchanged, digit = new colour. This is the diff-map the model is taught to produce.

This shape covers all 35 same-size micro families + 740 hand-written real ARC canonical solvers, all gate-verified.

## Diff-size grammar (proposed; proven on 3 micro families + 3 real ARC pilots)

```python
def solve(input_grid):
    T = infer_T(input_grid)            # T: structure (h, w, content_rule)
    return apply_T(input_grid, T)      # build fresh h x w grid, fill from T
```

**Public function signatures unchanged**: still `solve = apply_T(infer_T(g))`. The LoRA learns *one* top-level grammar.

What differs:
- **`infer_T` returns** a dict containing output geometry (`h`, `w`) plus content-rule parameters.
- **`apply_T` constructs** a new h×w grid rather than copying the input.

### Two content styles (each L1 family is one or the other)

**1. Gather** — output cell value comes from some input cell.
```python
# crop_to_bbox example
def infer_T(g):
    bg = most_common(g)
    cells = [(r, c) for r, c in nonbg(g)]
    r0, r1 = min(rs), max(rs); c0, c1 = min(cs), max(cs)
    return {"r0": r0, "c0": c0, "h": r1 - r0 + 1, "w": c1 - c0 + 1}


def apply_T(g, T):
    return [[g[T["r0"] + r][T["c0"] + c] for c in range(T["w"])]
            for r in range(T["h"])]
```
Covers: crop, scale, tile, reflect, transpose, rotate, extract-sub-region.

**2. Canvas + paint** — output built from scratch with new colours, possibly using gather from input as parameters.
```python
# 0520fde7 example (split + AND mask, 3x7 -> 3x3)
def infer_T(g):
    sep = next(c for c in range(W)
               if len({g[r][c] for r in range(H)}) == 1 and g[0][c] != 0)
    return {"sep": sep, "h": H, "w": sep}


def apply_T(g, T):
    sep = T["sep"]
    left = [row[:sep] for row in g]
    right = [row[sep + 1:] for row in g]
    h, w = len(left), len(left[0])
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if left[r][c] != 0 and right[r][c] != 0:  # AND
                out[r][c] = 2
    return out
```
Covers: comparison/AND/OR outputs, count-to-grid, classification-rendered-as-grid.

## SFT prompt evidence (key design choice)

Per-cell T is undefined when dimensions differ, so the prompt evidence is different:

| Track | Per-pair evidence shown |
|---|---|
| Same-size | `INPUT` + per-cell `T` (`.`/digit diff-map) |
| Diff-size | `INPUT` + `OUTPUT` + `SIZE H×W → h×w` |

Both use the same system prompt skeleton (the substrate goal) with one paragraph specific to each grammar explaining what `T` contains. The model learns *both* grammars; the system prompt cue tells it which to emit.

## What's been built and verified

| Layer | Same-size | Diff-size |
|---|---|---|
| L1 micro families | 32 (rays, lines, fills, components, symmetry, periodicity, gravity, drop, fence, flip, draw_bbox, marker-driven, etc.) | 3 (`crop_to_bbox`, `scale_2x`, `rotate_90`) |
| L1 SFT records | 7,680 | 720 |
| L1 contract gates | per-sample + family-contract, all pass | per-sample + family-contract, all pass |
| L2 real-ARC canonical solvers | 740 hand-written, validated | 3 pilots (`007bbfb7` fractal, `00576224` tile-with-mirror, `0520fde7` split+AND), all 6/6 across augmentation variants |
| Agent spec for swarm | not needed (already 740 written) | `canonical/diff_pilot/_AGENT_SPEC_DIFF.md` — 3 worked exemplars, contract pinned, tightened audit (`big_literal_max=8` for small outputs) |

## Open scope / what's not yet done

- **~361 of ~364 diff-size real ARC puzzles** still need canonical solvers (agent swarm work, spec ready).
- **Whether the LoRA learns to emit the diff-size grammar from only 720 L1 + 3 L2 examples** is empirically unknown until Run 1. The grammar is sound; the question is data sufficiency.

## What we're asking GPT to sanity-check

1. **Is the dual-grammar approach right** (same-size uses per-cell T; diff-size uses geometry+content T; same `solve = apply_T(infer_T(g))` shape, two system prompts), or should there be a single unified grammar that covers both?
2. **Is "gather vs canvas+paint" the right content-style split** for diff-size, or are there cases this doesn't cover cleanly?
3. **Is the SFT evidence right** for diff-size (INPUT + OUTPUT + SIZE), or is there a more useful aggregate-T encoding that would give the model more diagnostic signal than just "output looks like this"?
4. **Is a 720 L1 + 3 L2 budget plausible for the LoRA to learn the diff-size grammar**, given that 35 same-size families × 240 records taught the same-size grammar well, or should we delay Run 1 until the swarm produces more L2 diff-size solvers?

The goal is to ship Run 1 with what we have if the design is sound, and adjust if there's a sharper alternative.
