# Diff-Size Substrate — Spec v1 (draft for review)

**Status:** Designed, not yet implemented. Companion to the existing
same-size pixel substrate (`substrate.py:encode()`). Looking for sanity
check before adding to `substrate.py` and the SFT generator.

**Scope:** Defines the substrate representation used when a single
training/test pair has `input.shape != output.shape`. The pixel
substrate covers shape-preserving pairs; this spec covers everything
else.

---

## Why this exists

The current pixel substrate in `substrate.py:encode()` operates per-cell:

```
.       cell preserved (input[r,c] == output[r,c])
0..9    output cell is this color (different from input)
```

It is lossless and dense, but it assumes `input.shape == output.shape`.
Per-cell comparison is undefined when shapes differ — there is no
"input[r,c]" to pair with "output[r,c]" if the grids have different
dimensions.

About 33% of ARC puzzles have at least one differently-shaped pair.
Without a substrate for them, those puzzles get no Phase-1
representation training and the model has to interpret raw grid pairs
unaided.

Also: **shape-mismatch is a per-pair property, not a puzzle property.**
Some puzzles have `pair[0]` same-size and `pair[1]` diff-size. So the
substrate can't be selected per-puzzle — Python must dispatch at the
pair level via a single entry point (see "Dispatch" below).

---

## Design principles

1. **Variant pops, invariant fades.** Same principle as same-size: the
   model should be able to scan a substrate and instantly see which
   facts are stable across pairs and which change. In the pixel
   substrate this is achieved by `.` for unchanged cells (silent
   background) and digits for changes (foreground). The diff-size
   substrate achieves it at the *line* level via repeated relation
   tags.

2. **Pure mechanical, no heuristics.** Every value is `f(input, output)`
   computed by closed-form arithmetic or counting. No detectors, no
   pattern matching, no "I think this is a tiling." Deterministic
   tiebreaking conventions are allowed (same kind that exist in
   `background_of()` and `hierarchy_substrate()`); guesses about what
   the puzzle is doing are not.

3. **Lossy is fine.** Pixel substrate is lossless because per-cell
   information is finite and computable. Diff-size pairs cannot be
   reconstructed from aggregates, and that's accepted by design — the
   same trade-off that `hierarchy_substrate()` already makes.

4. **MECE.** Each field answers exactly one orthogonal question. No
   field is derivable from any other field in the same substrate. (An
   earlier draft included a "DIM_REL same/different" block that was
   strictly derivable from the dimensions themselves; that has been
   removed.)

---

## Format

A diff-size substrate is a short text block with two sections:

```
SIZE <H>x<W> -> <h>x<w>   h:<tag> w:<tag>
PALETTE
  <c0>  <in_count> -> <out_count>   <tag>
  <c1>  <in_count> -> <out_count>   <tag>
  ...
```

Where `<H>x<W>` is the input shape, `<h>x<w>` the output shape, each
`<tag>` is the output of `relate(a, b)` defined below, and the palette
lists every color appearing in either grid, sorted ascending by color
value.

### `relate(a, b)` — the only nontrivial helper

`relate` compresses a pair of nonnegative integers `(a, b)` into one
visible tag. Definition (closed-form, no branching on context):

```python
def relate(a: int, b: int) -> str:
    if a == 0 and b == 0:  return "="
    if a == 0:             return "new"
    if b == 0:             return "dropped"
    if a == b:             return "="
    if b % a == 0:         return f"×{b // a}"
    if a % b == 0:         return f"÷{a // b}"
    return f"{b - a:+d}"
```

Possible tag forms:

| Tag | Meaning | Condition |
|---|---|---|
| `=` | identical | `a == b` (or both zero) |
| `×N` | scaled up by N | `b == N * a`, integer `N > 1` |
| `÷N` | scaled down by N | `a == N * b`, integer `N > 1` |
| `+N` / `-N` | additive shift | no integer ratio applies |
| `new` | appeared | `a == 0 and b > 0` |
| `dropped` | gone | `a > 0 and b == 0` |

The order of checks is a deterministic tiebreaking rule: when both `×2`
and `+1` could describe `(1, 2)`, multiplicative wins. This is a
convention, not a heuristic — the function only knows two integers, not
what the puzzle is doing.

### SIZE line — what each piece means

```
SIZE 9x7 -> 3x1   h:÷3 w:÷7
```

- `9x7` — input H × W
- `3x1` — output h × w
- `h:÷3` — `relate(H, h)`. Reading: input height is 3× the output height.
- `w:÷7` — `relate(W, w)`. Reading: input width is 7× the output width.

When `H == h` and `W == w` the diff-size encoder should never be called
(the same-size encoder applies). Otherwise the two tags reveal whether
each axis scaled cleanly, scaled down, or shifted additively.

### PALETTE block

One row per color appearing in either grid, sorted by color value:

```
PALETTE
  2  24 -> 1   ÷24
  5  15 -> 1   ÷15
  8  24 -> 1   ÷24
```

Reading each row: `<color>  <input_count> -> <output_count>   <tag>`
where the tag is `relate(input_count, output_count)`. So `2  24 -> 1
÷24` means color 2 appeared 24 times in the input, 1 time in the
output, a 24× reduction.

Colors with zero in both grids are simply not listed.

---

## Worked example — the band-collapse puzzle

A typical diff-size puzzle: input is a 9×7 grid with three horizontal
bands of dominant colors; output is a 3×1 column listing each band's
dominant color from top to bottom.

**Input** (9×7, colors 2 / 8 / 5 in three rough bands):

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

**Substrate emitted by `diffsize_encode(input, output)`:**

```
SIZE 9x7 -> 3x1   h:÷3 w:÷7
PALETTE
  2  24 -> 1   ÷24
  5  15 -> 1   ÷15
  8  24 -> 1   ÷24
```

**What the model can read off it:**

- Output height is exactly input height divided by 3 (`h:÷3`).
- Output width is exactly input width divided by 7 (`w:÷7` — output is
  a single column).
- All three input colors survive (`-> 1` for every row, no `dropped`).
- No new colors appear (no `new` rows).
- The per-color reduction ratios are not uniform (24, 15, 24). If the
  rule were proportional scaling, all three would match the area ratio
  21×. They don't — the rule is selection, not scaling.
- Combined with the height ratio of 3 and three colors in the output,
  the model has strong signal toward "each output row picks one
  representative color per horizontal band."

The substrate never names that rule. It just makes the underlying facts
line up so the model can guess from a few pairs.

---

## Contrasting example — uniform tiling

A simpler puzzle: input is a 2×2 tile, output is the same tile repeated
3 times in each dimension (6×6 total).

**Input**:

```
79
43
```

**Output**:

```
797979
434343
979797
343434
797979
434343
```

**Substrate:**

```
SIZE 2x2 -> 6x6   h:×3 w:×3
PALETTE
  3  1 -> 9   ×9
  4  1 -> 9   ×9
  7  1 -> 9   ×9
  9  1 -> 9   ×9
```

**What the model reads off it:** every dimension scales by 3 (`h:×3`,
`w:×3`), and every color scales by 9 (`×9` down every palette row). The
area ratio is `3 × 3 = 9`, exactly matching the per-color ratio. The
repetition of `×9` is the invariant the model should latch onto:
*uniform scaling, palette preserved*. The actual rule (tiling, possibly
with row-shifts) needs cross-pair comparison to nail down, but the
single-pair substrate already pins the search to "the input is repeated
3×3 times".

Compare to the band-collapse substrate above: same skeleton, very
different *line-by-line pattern*. Uniform `×9` everywhere vs. mixed
`÷24 / ÷15 / ÷24`. The model learns to read the pattern of tags down
the page, not just individual values.

---

## Dispatch — `encode_auto(input, output)`

A single entry point picks per pair, with no caller knowledge of the
puzzle's structure:

```python
def encode_auto(inp, out):
    same = (len(inp) == len(out)) and (len(inp[0]) == len(out[0]))
    return encode(inp, out) if same else diffsize_encode(inp, out)
```

- `encode()` (the existing same-size pixel encoder) raises if shapes
  differ.
- `diffsize_encode()` (this spec) raises if shapes match.

The two functions have mutually exclusive domains; `encode_auto` is the
only branching point and it branches on a fact (`H == h and W == w`),
not on a guess.

This handles mixed-shape puzzles correctly: each pair gets the right
substrate independently. A puzzle with same-size `pair[0]` and
diff-size `pair[1]` produces a pixel grid for the first and a text
block for the second.

---

## What this does *not* do

- **Not lossless.** Given a substrate, you cannot reconstruct the input
  or output grids. This is intentional (matches `hierarchy_substrate`).
  No `diffsize_decode()` function.
- **Not spatial.** The substrate carries no per-cell information. If
  the rule depends on *where* in the input each color sat, the
  diff-size substrate alone won't show it. Per-grid hierarchy
  substrates (`H` task) can be computed on input and output
  independently to add some spatial signal, but they're a separate
  task.
- **Not cross-pair.** A single pair's substrate. Cross-pair invariance
  (the rule must work for all pairs of a puzzle) is the job of a
  multi-pair view, the analog of the existing `M` task tag for
  same-size.

---

## Open questions for review

**Q1. Is the SIZE-line `relate` tag sufficient, or should we also emit
the four raw numbers (`H, W, h, w`) explicitly?**
The line `SIZE 9x7 -> 3x1   h:÷3 w:÷7` includes both the absolute
shapes and the relational tags. The tag is derivable from the shapes
(`relate(9, 3) = ÷3`) — so it's *technically* redundant under MECE.
Argument for keeping it: it speeds up "variant pops" reading. Argument
against: violates MECE strictly. Likely keep but flag.

**Q2. Should the PALETTE sort be by color value or by descending
input count?**
Current spec: by color value ascending. Argument: consistent across
pairs of the same puzzle (color 3 always lands in the same row of the
substrate, even if its rank differs by pair). Argument against: count-
descending puts the rule-defining colors first. We picked stability
over salience; flag for review.

**Q3. Should `+N`/`-N` be expressed in absolute terms or as a signed
diff?**
Currently `relate(5, 3) -> "-2"` (signed). Alternative: `Δ-2` or
`5→3:diff-2`. Signed numbers are tightest but a leading `-` could
be confused with the substrate-grid digits in mixed contexts. Likely
keep signed but flag.

**Q4. Should we ever fall back to per-cell substrate even on
diff-size pairs, by padding or cropping the smaller grid?**
No — padding/cropping is a heuristic ("which alignment is right?")
and breaks the no-heuristics rule. The diff-size substrate stays
purely aggregate. Per-cell signal for diff-size, if needed, comes
from independent `hierarchy_substrate(input)` /
`hierarchy_substrate(output)`.

**Q5. Does this representation generalize to non-grid-shape outputs
(scalars, color lists, single colors)?**
Some ARC tasks output a single cell or a color name. Those are still
"grids" of shape `1x1` and the substrate works mechanically. But the
PALETTE row reading `÷24` for a `24 -> 1` reduction may not be the
most informative signal for a scalar-output puzzle. Acceptable for
v1; revisit if calibration shows it underperforming.

---

## What we want from external review

- Sanity check the alphabet. Are `=`, `×N`, `÷N`, `+N`/`-N`, `new`,
  `dropped` the minimal MECE set, or is there an obvious omission /
  overlap?
- The MECE audit. Anything in the SIZE or PALETTE block strictly
  derivable from anything else in the same block?
- The `relate()` tiebreaking order. Multiplicative-before-additive is
  the current rule. Is there a case where preferring additive would
  produce a more useful signal?
- Worked example coverage. The band-collapse and tiling examples
  bracket "selection" vs "uniform replication." Is there a third
  canonical class of diff-size transformation we should add an example
  for (e.g. extraction, indexing, projection)?
- Open Q1–Q5 above. Direct opinions welcome.

---

## What gets built if the spec passes review

1. `substrate.py`: add `diffsize_encode(inp, out) -> str` and the
   `relate(a, b)` helper. Add `encode_auto(inp, out)` dispatcher.
   Update `encode()` and `diffsize_encode()` docstrings to declare
   their mutually-exclusive domains.
2. `gen_phase1_data.py`: extend to emit a new task tag (next free
   letter — `N`?) whose target is a diff-size substrate. Use
   `encode_auto` at generation time so mixed-shape puzzles produce the
   right target per pair.
3. Optional: a `phase1_diffsize_multi_pair` task analogous to `M`,
   stacking diff-size substrates from all training pairs of a puzzle
   into a single record for cross-pair invariance training.
4. Docs: update `README.md` task-tag table and
   `research/Phase1_Substrate_Spec.md` to point at this spec for the
   diff-size half of the curriculum.
