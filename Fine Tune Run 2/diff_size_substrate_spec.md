# Diff-Size Substrate — Spec v2 (locked)

**Status:** Implemented in `substrate.py` (`relate`, `diffsize_encode`,
`encode_auto`) and verified against 5,786 real diff-size pairs across the
ARC corpus. Companion to the existing same-size pixel substrate
(`substrate.py:encode()`).

**Scope:** Defines the substrate emitted for an `(input, output)` pair
where `input.shape != output.shape`. The pixel substrate covers
shape-preserving pairs; this spec covers everything else. Dispatch is
per pair via `encode_auto`, so a puzzle with mixed-shape pairs produces
both substrate kinds, one per pair.

---

## Documentation notes (read these first)

- **`BG` is mechanical, not semantic.** It is the most-frequent color
  (ties broken by smaller numeric color), per `background_of()`. For
  some pairs the value is the human-intuitive background (color 0). For
  others — especially dense puzzles — `BG` can be any color and even
  differs between input and output. That is expected and correct under
  the frequency rule; do not patch it with heuristics.
- **The diff-size substrate is lossy and diagnostic.** There is no
  `diffsize_decode()` and there will not be one. Two distinct grids can
  share the same aggregate substrate. The substrate provides evidence,
  not a reconstruction recipe.
- **`T2` (substrate → output) does not apply to diff-size substrates.**
  T2 is only well-defined for the same-size pixel substrate, which is
  lossless. The dataset generator must skip T2 for diff-size pairs.
- **`ROWS` / `COLS` can be long by design.** On a 30×30 input each row
  produces one IN_DOM token and one IN_NZ token; the section is dense
  but readable. The token cost is paid in exchange for spatial signal
  the model would otherwise have to infer from raw grids. No truncation.

---

## Why this exists

The pixel substrate in `substrate.py:encode()` operates per cell:

```
.       cell preserved (input[r,c] == output[r,c])
0..9    output cell is this color (different from input)
```

It is lossless and dense, but it assumes `input.shape == output.shape`.
Per-cell comparison is undefined when shapes differ — there is no
`input[r,c]` to pair with `output[r,c]` if the grids have different
dimensions.

About 33% of ARC puzzles have at least one differently-shaped pair
(corpus-wide: 612 all-diff and 15 mixed out of 1920 source files; 5,786
diff-size pair instances out of 16,714 total pair instances). Without a
substrate for those pairs, the model has to interpret raw grid pairs
unaided.

Shape-mismatch is a **per-pair** property, not a puzzle property. Some
puzzles have `pair[0]` same-size and `pair[1]` diff-size. The substrate
is selected per pair via `encode_auto`, never per puzzle.

---

## Design principles

1. **Variant pops, invariant fades.** Same as same-size: a substrate
   should let the model scan and instantly see which facts are stable
   across pairs and which change. The pixel substrate achieves this
   per-cell (via `.` for unchanged, digit for changed). The diff-size
   substrate achieves it at the *line* level — when every PALETTE row
   reads `×9` the model sees uniform scaling at a glance; when row
   dominants spell `0 4 0 6 0 8 0` the model sees a 1-of-3 selection
   pattern.

2. **Pure mechanical, no heuristics.** Every value is `f(input, output)`
   computed by closed-form arithmetic or counting. No detectors, no
   pattern matching, no "I think this is a tiling." Deterministic
   tiebreaking conventions are allowed; guesses are not.

3. **Lossy is fine.** Diff-size pairs cannot be reconstructed from
   aggregates; that is accepted by design. The substrate exists to make
   rule induction easier, not to reproduce the output.

4. **Fixed section order.** Sections always appear in the same order
   (`SIZE`, `BG`, `PALETTE`, `ROWS`, `COLS`, `BBOX`) so the model can
   key on layout rather than headings.

---

## Format

```
SIZE <H>x<W> -> <h>x<w>   h:<rel> w:<rel>
BG <in_bg> -> <out_bg>   <rel>

PALETTE
  <color> <in_count> -> <out_count> <rel>
  ...

ROWS
  IN_DOM:  <per-row dominant colors of input, space-separated>
  OUT_DOM: <per-row dominant colors of output>
  IN_NZ:   <per-row non-input-bg cell counts>
  OUT_NZ:  <per-row non-output-bg cell counts>

COLS
  IN_DOM:  <per-col dominant colors of input>
  OUT_DOM: <per-col dominant colors of output>
  IN_NZ:   <per-col non-input-bg cell counts>
  OUT_NZ:  <per-col non-output-bg cell counts>

BBOX
  <color> in:<bbox> out:<bbox>
  ...
```

Sorting and ordering:

- `PALETTE` and `BBOX`: ascending by color value. This is **stability,
  not salience** — color 3 always lands in the same row of the
  substrate across pairs of the same puzzle, which matters for
  multi-pair learning.
- `ROWS` and `COLS`: preserve natural row/col order.
- `bbox` format: `r<r0>-<r1>,c<c0>-<c1>` for present, `none` for absent.

### `relate(a, b)` — the only nontrivial helper

```python
def relate(a: int, b: int) -> str:
    if a == 0 and b == 0: return "="
    if a == 0:            return "new"
    if b == 0:            return "dropped"
    if a == b:            return "="
    if b % a == 0:        return f"×{b // a}"
    if a % b == 0:        return f"÷{a // b}"
    return f"Δ{b - a:+d}"
```

| Tag | Meaning | Condition |
|---|---|---|
| `=` | identical | `a == b` (or both zero) |
| `×N` | scaled up by integer N | `b == a * N`, `N > 1` |
| `÷N` | scaled down by integer N | `a == b * N`, `N > 1` |
| `Δ±N` | additive shift | no integer ratio applies |
| `new` | appeared from zero | `a == 0 and b > 0` |
| `dropped` | gone to zero | `a > 0 and b == 0` |

Multiplicative-before-additive is the tiebreaking rule: `relate(1, 2)`
returns `×2`, not `Δ+1`. This is a convention, not a heuristic — the
function only knows two integers, not what the puzzle is doing.

`relate` is used in three places: SIZE dim tags, BG tag, and PALETTE
count deltas. It is intentionally the same function in all three so the
model sees one consistent vocabulary.

### Per-row / per-col dominant

For each row (or column):

1. Count colors.
2. If any non-background color appears, restrict to those.
3. Pick the most-frequent color in the (possibly restricted) set.
4. Tie-break by smaller numeric color.

Input rows use `in_bg`, output rows use `out_bg`. The
"prefer non-background" rule surfaces the foreground signal when the
background dominates the cell count; it falls through to the background
when the row contains only background, which is itself signal.

### Non-bg count

For each row (or column), the count of cells whose value differs from
the relevant background.

### BBOX

For each color appearing in either grid (sorted ascending by color):

```
<color> in:<bbox-or-none> out:<bbox-or-none>
```

A `bbox` is the inclusive `(min_row, max_row, min_col, max_col)` of the
color's occurrences in that grid, rendered `r<r0>-<r1>,c<c0>-<c1>`. If
the color does not appear in a grid, that side is `none`.

---

## Worked example — band collapse

**Input** (9×7):

```
2222222
2222222
2222222
2888228
8888888
8888888
8885588
5855555
5555555
```

**Output** (3×1):

```
2
8
5
```

**Substrate:**

```
SIZE 9x7 -> 3x1   h:÷3 w:÷7
BG 2 -> 2   =

PALETTE
  2 24 -> 1 ÷24
  5 15 -> 1 ÷15
  8 24 -> 1 ÷24

ROWS
  IN_DOM:  2 2 2 8 8 8 5 5 5
  OUT_DOM: 2 8 5
  IN_NZ:   0 0 0 5 7 7 5 6 7
  OUT_NZ:  0 1 1
  ...
```

The model reads off: height divides by 3, width divides by 7, all three
colors survive at count 1, and the per-row dominant pattern
`2 2 2 8 8 8 5 5 5` lines up exactly with the three output colors
`2 8 5` — strong signal toward "each output row picks one color per
horizontal band."

The substrate never names the rule. It makes the underlying facts line
up so the model can guess from a few pairs.

---

## Contrasting example — uniform tiling

**Input** (2×2): `79/43`. **Output** (6×6): the same tile repeated 3×3.

```
SIZE 2x2 -> 6x6   h:×3 w:×3
BG 3 -> 3   =

PALETTE
  3 1 -> 9 ×9
  4 1 -> 9 ×9
  7 1 -> 9 ×9
  9 1 -> 9 ×9
```

Every PALETTE row is `×9`; every dim tag is `×3`. The repeated `×9` is
the invariant the model latches onto: *uniform scaling, palette
preserved*. The actual rule (tiling, possibly with row-shifts) still
needs cross-pair comparison, but the substrate already pins the search
to "input repeated 3×3 times."

The contrast with the band-collapse substrate is the model's training
signal: same skeleton (SIZE + BG + PALETTE + ROWS + COLS + BBOX), very
different *line-by-line pattern*. Uniform `×9` everywhere vs. mixed
`÷24 / ÷15 / ÷24`. The model learns to read the pattern of tags down
the page, not just individual values.

---

## Dispatch — `encode_auto(input, output)`

```python
def encode_auto(inp, out):
    same = (len(inp) == len(out)) and (len(inp[0]) == len(out[0]))
    return encode(inp, out) if same else diffsize_encode(inp, out)
```

- `encode()` returns a `Substrate` (`List[List[str]]`); raises if shapes
  differ.
- `diffsize_encode()` returns a `str`; raises if shapes match.
- `encode_auto` is the only branching point and it branches on a fact
  (`H == h and W == w`), not on a guess. Callers disambiguate the
  return type by `isinstance(result, str)`.

Mixed-shape puzzles produce the right substrate per pair, automatically.

---

## What this does *not* do

- **Not lossless.** Given a substrate, you cannot reconstruct the input
  or output grids. No `diffsize_decode()` function exists or will.
- **Not spatial in the pixel sense.** The substrate carries no per-cell
  information for an arbitrary pair of unaligned grids. ROWS/COLS and
  BBOX give *aggregate* spatial signal (which row had a non-bg cell,
  where each color sits), but they don't tell you which pixel maps to
  which.
- **Not cross-pair.** A single pair's substrate. Cross-pair invariance
  (the rule must work for all pairs of a puzzle) is the job of the
  multi-pair `O` task tag (= "all pairs → all auto-substrates"),
  which composes per-pair substrates from `encode_auto`.

---

## Task tags (Phase 1 vocabulary)

| Tag | Pair count | Substrate format | Notes |
|---|---|---|---|
| `T1` | 1 | per-pair via `encode_auto` | "pair → substrate" literacy |
| `T2` | 1 | same-size pixel only | "input + substrate → output"; **does not apply to diff-size** |
| `T3` (aka `O`) | all train pairs | per-pair via `encode_auto` | "all pairs → all auto-substrates" |
| `T4` | N-1 worked + 1 cold | per-pair via `encode_auto` | analogy: predict the cold pair's substrate |
| `T5` | all train pairs + test input | per-pair via `encode_auto` | predict the **test substrate** |
| `T6` | all train pairs + test input | none (output grid is the target) | direct output prediction |

The `N` tag (= diff-size aggregate substrate alone) is the single-pair
output of `diffsize_encode`; it is the diff-size half of what `T1`
produces. The `O` tag covers all pairs of a puzzle with auto-dispatch
per pair.

---

## What got built

1. `substrate.py`:
   - `relate(a, b) -> str`
   - `diffsize_encode(inp, out) -> str` (raises on same-shape inputs)
   - `encode_auto(inp, out)` (per-pair dispatch)
   - Removed legacy `encode_structure` and `encode_any` (the v1 names
     that nothing external referenced).
2. `scripts/test_diffsize_substrate.py` — exercises the three spec
   examples, `relate()` table, and dispatch/domain-rule invariants.
   Exit-0 regression test.
3. Repo-wide scan against `data/` and `Fine Tune Run 2/puzzles/`
   confirms: 10,928 same-size + 5,786 diff-size pairs encode without
   error, with all required sections present in every diff-size
   substrate.
