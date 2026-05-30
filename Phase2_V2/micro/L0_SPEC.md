# L0 Build Spec — Coordinate Ontology Layer (operational)

L0 = static grid atoms. **No transformations.** L0 teaches the model the
coordinate vocabulary it will use in L1 and L2 solvers. Atom definitions are
locked in [`CONTRACTS_L0.md`](CONTRACTS_L0.md); this doc is the operational
build plan.

## What L0 *is*
A coordinate-algebra layer. Every L0 record exercises **one** library call over
a static grid (no rule to infer, no transformation to apply) and renders the
result as a grid.

## What L0 is NOT
- **No transformations** — no ray, flood, fill, move, draw, rotate, flip, scale,
  repair, recolor, copy, delete, select, sort. (Those live in L1+; see
  `CONTRACTS.md` for the 35 L1 families.)
- **No composition** — each L0 record exercises ONE library call.
- **No grammar drift** — all outputs are grids; solver shape = library-call +
  render. No tuple/list/dict outputs at the top level.

---

## Output grammar (locked, same as L1/L2)

```python
def solve(input_grid):
    result = LIBRARY_CALL(input_grid)        # one L0 library atom invoked
    H, W = len(input_grid), len(input_grid[0])
    out = [[0] * W for _ in range(H)]         # blank canvas
    for (r, c) in result:                     # render the structure as a mask
        out[r][c] = MARK                      # marker colour = "this is in the set"
    return out
```

Same top-level grammar as L1 and L2: `solve: grid → grid`. The body invokes ONE
library function and renders its output. **No `infer_T`/`apply_T` scaffold here**
— L0 is *computation + render*, not transformation inference. (L1 and L2 keep
the `infer_T`/`apply_T` scaffold; L0 is the simpler base case.)

---

## The shared library — `Phase2_V2/micro/lib/grid_ops.py`

**L0 spec ≡ library spec.** Each atom in `CONTRACTS_L0.md` is one library
function. This file is the **central artifact** that L0/L1/L2 all use.

### Detectors
```python
def bg(g) -> int                                       # most common colour (caveat: declared not assumed)
def cells_of_color(g, color) -> set[tuple[int,int]]
def nonbg_cells(g) -> set[tuple[int,int]]
def find_components(g, conn: int) -> list[set]         # 4 or 8 — must be passed
def find_largest_component(g, conn: int) -> set
def find_blob(g, conn: int) -> set
def find_horizontal_line(cells) -> set | None
def find_vertical_line(cells) -> set | None
def find_diagonal(cells) -> set | None
def find_hollow_rectangle(g) -> dict | None            # {top, left, bottom, right, color, cells}
def find_filled_rectangle(g) -> dict | None
def find_u_cup(g) -> dict | None                       # {left_wall, right_wall, floor, interior, rim, color}
def find_ring(g) -> set | None
def find_seed(g, where: str) -> tuple | None           # "border" / "corner" / "interior"
def find_marker(g) -> tuple | None                     # the rarest non-bg single cell
def find_periodic_tile(g) -> tuple | None              # (pr, pc, template_dict)
```

### Coordinate operations
```python
def bbox(cells) -> tuple[int,int,int,int]              # (top, left, bottom, right)
def anchor(cells, kind="bbox_top_left") -> tuple
def boundary_of(cells, conn: int) -> set               # cells of `cells` touching outside
def interior_of(cells, conn: int) -> set               # object_interior (non-boundary cells)
def enclosed_region(g, conn: int) -> set               # bg cells NOT border-reachable
def holes(g, conn: int) -> list[set]                   # list of enclosed regions
def neighbors4(r, c) -> list[tuple]
def neighbors8(r, c) -> list[tuple]
def edge_cells(H, W, side: str) -> list[tuple]         # "top" / "bottom" / "left" / "right"
def corner_cells(H, W) -> list[tuple]
```

### Predicates
```python
def is_line(cells) -> bool
def is_horizontal_line(cells) -> bool
def is_vertical_line(cells) -> bool
def is_diagonal(cells) -> bool
def is_axis_aligned(cells) -> bool
def is_symmetric(cells, axis: str) -> bool
```

Predicates are used **inside detectors/solvers**; they don't get their own L0
families (an L0 family needs a renderable output, and a boolean isn't one).

---

## L0 generator families (~17, each exercises one library call)

Each family is structurally identical to the L1 micros: a generator (`generate`,
`_instance`, `canonical_solver`) + the same per-sample gate + the contract
validator. Mark colour for the rendered mask: a constant (e.g. `1`) by default
so the output is unambiguous.

| # | family | library call exercised | output renders |
|---|---|---|---|
| 1 | `l0_bg_detection` | `bg(g)` + `nonbg_cells(g)` | mask: non-bg cells → 1 |
| 2 | `l0_color_class` | `cells_of_color(g, c)` | mask of one target colour |
| 3 | `l0_components_4` | `find_components(g, 4)` | each component → unique label |
| 4 | `l0_components_8` | `find_components(g, 8)` | each component → unique label |
| 5 | `l0_bbox` | `bbox(nonbg_cells(g))` | bbox perimeter highlighted |
| 6 | `l0_boundary` | `boundary_of(cells, 4)` | boundary cells marked |
| 7 | `l0_interior_object` | `interior_of(cells, 4)` | object-interior marked |
| 8 | `l0_interior_enclosed` | `enclosed_region(g, 4)` | enclosed bg cells marked |
| 9 | `l0_hollow_rectangle` | `find_hollow_rectangle(g)` | mark just the outline |
| 10 | `l0_filled_rectangle` | `find_filled_rectangle(g)` | mark the solid rect |
| 11 | `l0_u_cup` | `find_u_cup(g)` | mark walls + floor (NOT fill) |
| 12 | `l0_ring` | `find_ring(g)` | mark the ring cells |
| 13 | `l0_seed` | `find_seed(g, "border")` | highlight the seed cell |
| 14 | `l0_marker` | `find_marker(g)` | highlight the marker cell |
| 15 | `l0_periodic_tile` | `find_periodic_tile(g)` | mark one period unit |
| 16 | `l0_edge` | `edge_cells(H, W, side)` | mark the requested edge |
| 17 | `l0_corners` | `corner_cells(H, W)` | mark the 4 corners |

(Variants — e.g., `find_seed` at edge vs corner — covered by tiers 0/1/2
inside a single family.)

---

## Training record format (same as L1)

3–4 train pairs + 1 test per task. Each pair shown as INPUT + per-cell T. The
per-cell T encoding works cleanly: `.` for cells the solver leaves at 0, digit
for cells it marks.

---

## File layout

```
Phase2_V2/micro/
  CONTRACTS_L0.md           ← locked atom definitions (verbatim)
  L0_SPEC.md                ← this file: operational build plan
  lib/
    grid_ops.py             ← the shared library (L0 spec ≡ this code)
  L0/
    generators/             ← 17 L0 generator modules
    solvers/                ← written by each generator's canonical_solver()
    tasks/                  ← validated tasks (per family)
    sft/                    ← SFT records (per family)
    _validation.json
    MANIFEST.txt
```

---

## Gates (same two layers as L1)

1. **Per-sample** (`build_micro.py`): runs the canonical solver vs ground truth
   on every train/test pair in a fresh subprocess + AST audit. No pass → no
   task on disk.
2. **Family-contract** (`validate_contracts.py`): preconditions per L0 family.
   E.g. for `l0_seed`: exactly one border non-bg cell. For `l0_components_4`:
   labels are unambiguous (no tie that the renderer would have to break
   arbitrarily). For `l0_periodic_tile`: a unique minimal period exists.

---

## Build order

1. **Write `lib/grid_ops.py`** — implement the ~30 library functions per
   `CONTRACTS_L0.md`. This is the central artifact; everything else uses it.
2. **Build the 17 L0 generator families.** Each is small (~50–80 lines):
   generator + canonical solver that calls the library + renders.
3. **Gate every family** through the per-sample gate + the contract validator.
4. **Build SFT records** via `build_micro_sft.py` for each family.
5. **Refactor L1 micros** (recommended) to call `lib/grid_ops.py` inside their
   `infer_T` bodies — this is what reinforces the vocabulary across layers, and
   it's what makes "L0 ⊂ L1 ⊂ L2" true in practice, not just on paper.

---

## Acceptance criteria for L0 "done"

- `lib/grid_ops.py` implements all ~30 library functions, each with a clear
  type signature matching `CONTRACTS_L0.md`.
- 17 L0 families, each 60/60 through both gates.
- Every L0 solver follows the locked solver shape (library call + render).
- ≥1 L1 family has been refactored to call `grid_ops.py` end-to-end, proving
  the library is the same one L1 uses (no parallel implementations).

Once this is in place, the substrate is complete enough to start the merged
training set per `SOLVER_LORA_PLAYBOOK.md`.
