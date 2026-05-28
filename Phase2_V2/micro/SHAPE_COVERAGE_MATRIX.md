# Shape Coverage Matrix

Planning document. **No code in this commit — just the substrate audit.**

## Framing (locked)

- **Invariant** = the structural definition of the shape. Cross it, you're in a different class.
- **Within-class physics** = operations that produce variants WHILE PRESERVING the invariant. Variants are exactly the closure of the invariant under these operations; the variant set isn't a separate column.
- **Cross-class transitions** = operations that BREAK the invariant. They produce a different shape and therefore belong to a different object's family — not this object's gaps.
- **Shapes are MECE.** A U-cup whose top gets enclosed is a *hollow_rectangle*, not a transformed U-cup. Filling the interior of a hollow_rectangle is a *filled_rectangle*.

## Read of our existing 35 L1 micros, sorted by object class

### seed *(single non-bg cell, location-typed: border / corner / interior)*
- **Invariant**: a single non-background cell; its colour and location are the only state.
- **Within-class physics (have)**: `ray_to_edge`, `ray_until_blocker`, `ray_diag_to_edge`, `ray_diag_until_blocker`, `cross_from_seed`, `star_from_seed`, `flood_from_seed`, `flood_from_seed_8`, `ball_roll`, `maze_runner`. *(In all of these the seed itself is preserved in the output; the operations emit new structure from it.)*
- **Within-class gaps**: `move_seed`, `count_seeds` (multi-seed grids), `recolor_seed`.
- **Cross-class transitions**: surround it with walls → seed becomes the interior of an enclosure; flood until the seed is part of a larger blob → seed disappears into a blob.

### u_cup *(two equal-length vertical walls + horizontal floor + open top, single colour)*
- **Invariant**: two walls of length L, floor connecting their bottoms, **top row between walls is background**, single colour.
- **Within-class physics (have)**: `u_cup_fill` (fills interior to rim — interior changes, structural cup invariant preserved).
- **Within-class gaps**: `rotate_u_cup` (sideways / inverted U), `move_u_cup`, `scale_u_cup` (vary L), `recolor_u_cup`, `count_u_cups`.
- **Cross-class transitions**: close the top → `hollow_rectangle`. Remove a wall → `L_shape` or two parallel lines. Remove the floor → two parallel vertical lines.
- **Status**: **starving** — only 1 physic; 5 obvious gaps.

### diagonal *(contiguous 1-cell-thick line where `r-c=k` or `r+c=k`, single colour)*
- **Invariant**: contiguous diagonal cells, single colour, 1-cell-thick.
- **Within-class physics (have)**: none, as a diagonal *object*. (`ray_diag_*` produces a diagonal from a seed; `sandwich_fill` / `complete_line` fill between diagonal endpoints — those treat the endpoints as the object, not the diagonal as one.)
- **Within-class gaps**: `extend_diagonal`, `rotate_diagonal` (main ↔ anti), `move_diagonal`, `recolor_diagonal`, `delete_diagonal`, `count_diagonals`.
- **Cross-class transitions**: thicken → `blob`. Bend → no longer a diagonal (becomes a `path`). Break into segments → multiple disjoint cells.
- **Status**: **starving** — 0 physics. Genuine gap.

### line *(contiguous 1-cell-thick row OR column, single colour)*
- **Invariant**: contiguous cells with constant row OR constant column, single colour, 1-cell-thick.
- **Within-class physics (have)**: emitted by `ray_to_edge` / `ray_until_blocker` (seed → line). Filled by `complete_line` / `sandwich_fill` when endpoints define an H or V line.
- **Within-class gaps**: `extend_line`, `move_line`, `rotate_line` (H ↔ V), `recolor_line`, `delete_line`, `count_lines`.
- **Cross-class transitions**: thicken → `blob`. Add a perpendicular line → `plus` or `cross`.
- **Status**: physics are emit-only; no line-as-object operations yet.

### two_endpoints *(two same-colour cells collinear in row, column, or diagonal)*
- **Invariant**: exactly two non-bg cells of the same colour, collinear.
- **Within-class physics (have)**: `complete_line` (fill between), `sandwich_fill` (fill between for all such pairs).
- **Within-class gaps**: `extend_beyond_endpoints`, `recolor_endpoints`, `count_endpoint_pairs`.
- **Cross-class transitions**: filling between IS the cross-class transition → result is a `line` or `diagonal`. (So `complete_line` is technically class-changing two_endpoints → line.)

### blob *(connected same-colour non-bg cells, no required geometric shape)*
- **Invariant**: connected (4- or 8-) under a *declared* connectivity, single colour.
- **Within-class physics (have)**: `component_4conn`, `component_8conn`, `extract_largest_recolor`, `recolor_by_marker`, `move_to_marker`, `copy_to_markers`, `drop_to_floor`, `fence_4conn`, `fence_8conn`, `draw_bbox`. (Plus `boundary_mask` — see cross-class.)
- **Within-class gaps**: `scale_blob`, `rotate_blob`, `count_blobs`, `sort_blobs_by_size`.
- **Cross-class transitions**: `boundary_mask` → blob becomes its outline (`ring`). `fill` would turn a hollow blob into a `filled_rect`-like solid; we don't have that.
- **Status**: **well-served** (most operations are here).

### hollow_rect *(rectangle outline; 4 edges present, interior is bg, single colour)*
- **Invariant**: outline cells at min/max row AND min/max col; interior is background; single colour.
- **Within-class physics (have)**: `fence_4conn`, `fence_8conn` (outer fence in colour 8), `draw_bbox` (trivially identifies itself), `boundary_mask` (already hollow → near no-op).
- **Within-class gaps**: `rotate_hollow_rect`, `move_hollow_rect`, `scale_hollow_rect`, `recolor_hollow_rect`, `count_hollow_rects`.
- **Cross-class transitions**: `fill_enclosed` → `filled_rect`. Open one edge → `u_cup` (if 3 edges remain in U formation) or `L_shape`.
- **Status**: outline-only physics; transformation operations missing.

### filled_rect *(solid rectangle, every cell in bbox same non-bg colour)*
- **Invariant**: every cell in bbox shares one non-bg colour.
- **Within-class physics (have)**: inherits everything from `blob` (it IS a blob, with a stricter invariant).
- **Within-class gaps**: `rotate_filled_rect` (rectangles are rotation-defining), `scale_filled_rect`, `count_filled_rects`.
- **Cross-class transitions**: `boundary_mask` → `hollow_rect`. Crop a piece → `L_shape`. Punch a hole → annulus (a ring-like shape).

### ring / closed_outline *(arbitrary closed 1-cell-thick boundary enclosing an interior)*
- **Invariant**: a closed loop of cells (every cell has exactly two neighbours along the loop, single colour); encloses a non-empty bg interior.
- **Within-class physics (have)**: `fill_enclosed` (generalised — works on any closed shape). `fence_4conn`/`fence_8conn` work outside.
- **Within-class gaps**: `rotate_ring`, `move_ring`, `scale_ring`, `recolor_ring`, `count_rings`.
- **Cross-class transitions**: `fill_enclosed` → solid blob. Break the loop → an open `path`.

### periodic_tile *(repeating sub-pattern with period (pr, pc))*
- **Invariant**: there exists (pr, pc) such that `g[r][c] = template[r%pr][c%pc]` for all non-hole cells.
- **Within-class physics (have)**: `periodic_repair` (restore holes using the tile), `periodic_extension` (row-only extension along a periodic phase).
- **Within-class gaps**: `extract_tile` (return the period unit), `identify_period` (detect (pr, pc)), `rotate_tile`, `scale_tile`, `change_period` (re-tile at different period).
- **Cross-class transitions**: corrupt enough cells → no detectable period → grid becomes generic / non-periodic.

### any_grid *(no shape requirement — whole-grid geometry)*
- **Invariant**: just a grid. No structural constraint.
- **Within-class physics (have)**: `flip_horizontal`, `flip_vertical`, `rotate_90`, `scale_2x`, `crop_to_bbox`, `symmetry_complete_vertical`, `symmetry_complete_horizontal`, `gravity_water` (per-column settling — operates on cells, not a defined shape).
- **Within-class gaps**: `shift / translate`, `transpose`, `colour_permute` (swap colours per a learned map), `tile_grid` (repeat the whole grid k times in each direction).
- **Cross-class transitions**: none — `any_grid` is the universal class; any output IS a grid.

### marker *(meta-cell — NOT a shape with its own physics)*
- A marker is a single cell that **annotates another object**: its colour conveys information (target colour for `recolor_by_marker`, fence colour was named by the marker before we switched to fixed 8, etc.), its position is an anchor or destination.
- **Marker does not have within-class physics.** Operations that consume markers (`move_to_marker`, `copy_to_markers`, `recolor_by_marker`, `extract_largest_recolor`) are physics of OTHER objects that *use* a marker as input. Listing markers here is for completeness, not for gap analysis.

---

## What this audit reveals

### The clearly-starving classes (need new L1 physics urgently)
- **u_cup** — only 1 physic, 5 obvious gaps.
- **diagonal** — 0 physics as an object; everything we have is seed→diagonal emission.
- **line** — only emission and fill-between; no line-as-object physics.
- **hollow_rect / filled_rect / ring** — outline-/fill-focused; rotate/scale/count missing.
- **periodic_tile** — repair and row-extension only; can't extract or transform tiles.

### The well-served classes
- **seed** — 10 physics, covers ray / flood / radiate / roll across both connectivities and edge/corner/interior positions.
- **blob** — 10 physics, the broadest coverage.
- **any_grid** — 8 whole-grid transforms.

### The L0 gap
- **Detectors are mostly missing** — we inline detection inside each L1 micro instead of calling a named library function. Only `find_components` exists in `lib/grid_ops.py`. **Every object class above needs its detector (`detect_u_cup`, `detect_diagonal`, `detect_seed`, `detect_blob`, `detect_hollow_rect`, `detect_filled_rect`, `detect_ring`, `detect_periodic_tile`, `detect_line`, `detect_two_endpoints`)**, each returning `list[record]` per the canonical schema.

### Cross-class transitions to be aware of
These pairs of (operation, source-class → target-class) are the *type promotions* in the substrate. Useful for L2/L3 composition reasoning:
- `fill_enclosed`: hollow_rect → filled_rect; ring → blob
- `boundary_mask`: blob → ring; filled_rect → hollow_rect
- `close_top`: u_cup → hollow_rect
- `open_top`: hollow_rect → u_cup (we don't have this as a generator op)
- `thicken`: line/diagonal → blob
- `corrupt`: periodic_tile → generic grid

---

## Implied next-step priorities (not committed — for review)

1. **Build the 10 L0 detectors** as the highest-leverage artifact (each is the *reuse handle* for transfer).
2. **Fill the diagonal physics gap** — it's a major MECE class with literally zero current physics. Builds: `extend_diagonal`, `rotate_diagonal`, `move_diagonal`, `recolor_diagonal`.
3. **Fill the u_cup physics gap** — `rotate_u_cup`, `move_u_cup`, `scale_u_cup`.
4. **Refactor existing L1 micros to call L0 detectors** — this is what turns "L0 ⊂ L1" from a claim into observed code reuse.
5. **Build line-as-object physics** — currently lines only come out of seeds.

Coverage = sum across (object × physic) cells. Right now we're at **35 cells filled**; gaps named above push the target to roughly **60–70**. That's the substrate budget for run-1 corpus completion.
