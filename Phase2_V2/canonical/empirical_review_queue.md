# Weird puzzles — review queue

**TAIL (54 puzzles)** — solvers with a structural signature unique to them. Each is a candidate new primitive or a rare composition.

**UNCLUSTERED (223 puzzles)** — solvers with NO detected structural features. Could be bespoke per-puzzle logic, or patterns the analyzer missed.

Each entry: puzzle ID — features — hint (docstring / first code line).

---

## TAIL (unique signatures, your first review)

- **`4c416de3`** [BG_COUNTER, COL_SETTLE, CONN4_TUPLE, CONN8_TUPLE, COUNTER_LIB, MAX_BY_LEN, STACK_DFS]
   ↳ 8-connected components of cells where accept(value) is True, grouped by

- **`1190bc91`** [COL_SETTLE, CONN4_TUPLE, MAX_BY_LEN, QUEUE_BFS, ROT90_IDX, STACK_DFS]
   ↳ The input contains:

- **`264363fd`** [BG_COUNTER, COL_SETTLE, CONN4_TUPLE, CONN8_TUPLE, COUNTER_LIB, STACK_DFS]
   ↳ Latent mask {(r,c): color}.

- **`dd6b8c4b`** [BG_COUNTER, BORDER_LOOP, CONN4_TUPLE, COUNTER_LIB, QUEUE_BFS, STACK_DFS]
   ↳ Structure of the task (all color roles inferred from input structure, no literals):

- **`fafd9572`** [BBOX, BG_COUNTER, CONN4_TUPLE, CONN8_TUPLE, MAX_BY_LEN, STACK_DFS]
   ↳ Structure:

- **`16b78196`** [BBOX, CONN4_TUPLE, FROZENSET_KEY, ROT90_IDX, VFLIP_IDX]
   ↳ -----------------------------------

- **`8e5c0c38`** [BG_COUNTER, CONN8_TUPLE, COUNTER_LIB, FROZENSET_KEY, STACK_DFS]
   ↳ background. Each object is "almost" left-right (mirror) symmetric. For every

- **`9720b24f`** [BG_COUNTER, CONN4_TUPLE, CONN8_TUPLE, COUNTER_LIB, QUEUE_BFS]
   ↳ Background is 0 when present, else the most common color.

- **`a395ee82`** [BG_COUNTER, COUNTER_LIB, GCD, MAX_BY_LEN, STACK_DFS]
   ↳ 8-connected components of all non-background cells.

- **`b230c067`** [CONN4_TUPLE, CONN8_TUPLE, FROZENSET_KEY, STACK_DFS, TUPLE_NORMALIZE]
   ↳ 8-connected components of color-8 cells.

- **`df8cc377`** [BG_COUNTER, CONN4_TUPLE, CONN8_TUPLE, COUNTER_LIB, STACK_DFS]
   ↳ H, W = len(grid), len(grid[0])

- **`0e206a2e`** [BG_COUNTER, COUNTER_LIB, FROZENSET_KEY, STACK_DFS]
   ↳ ----

- **`1acc24af`** [BBOX, CONN4_TUPLE, FROZENSET_KEY, STACK_DFS]
   ↳ Same-size scene with two regions sharing a horizontal ground line:

- **`228f6490`** [CONN4_TUPLE, COUNTER_LIB, FROZENSET_KEY, STACK_DFS]
   ↳ ----

- **`320afe60`** [BG_COUNTER, CONN4_TUPLE, QUEUE_BFS, STACK_DFS]
   ↳ The background is the most common color (4). The grid contains several blue (1)

- **`321b1fc6`** [BG_COUNTER, CONN4_TUPLE, FROZENSET_KEY, STACK_DFS]
   ↳ 4-connected components of non-background cells.

- **`522fdd07`** [BG_COUNTER, COL_SETTLE, CONN4_TUPLE, STACK_DFS]
   ↳ Latent mask: each solid square is resized about its center.

- **`5adee1b2`** [CONN4_TUPLE, CONN8_TUPLE, QUEUE_BFS, STACK_DFS]
   ↳ 8-connected single-color connected components (non-zero).

- **`6aa20dc0`** [BG_COUNTER, COL_SETTLE, COUNTER_LIB, STACK_DFS]
   ↳ Latent mask: dict {(r,c): new_color} of cells to overwrite.

- **`6e19193c`** [CONN4_TUPLE, CONN8_TUPLE, RAY_STEP, STACK_DFS]
   ↳ Return list of (color, cells) for 8-connected non-zero components.

- **`753ea09b`** [BG_COUNTER, CONN4_TUPLE, MAX_BY_LEN, QUEUE_BFS]
   ↳ Each grid has three colors: a background (most common), a "structure" color and

- **`7ddcd7ec`** [BBOX, BG_COUNTER, CONN8_TUPLE, RAY_STEP]
   ↳ Infer a latent mask {(r,c): color} of cells to paint.

- **`825aa9e9`** [CONN4_TUPLE, CONN8_TUPLE, COUNTER_LIB, STACK_DFS]
   ↳ Return (bg, struct, obj) colors, or None if the 3-color layout is absent.

- **`902510d5`** [BG_COUNTER, COUNTER_LIB, MAX_BY_LEN, STACK_DFS]
   ↳ - The grid contains one large connected diagonal "blob" (the largest 8-connected

- **`9b2a60aa`** [CONN4_TUPLE, CONN8_TUPLE, MAX_BY_LEN, STACK_DFS]
   ↳ ----

- **`e76a88a6`** [BG_COUNTER, CONN4_TUPLE, MAX_BY_LEN, STACK_DFS]
   ↳ non-background, non-gray colors) and one or more solid gray (5) rectangular

- **`55783887`** [BG_COUNTER, COUNTER_LIB, RAY_STEP]
   ↳ - Background = most common color. Foreground markers are single colored cells

- **`62ab2642`** [CONN4_TUPLE, MAX_BY_LEN, STACK_DFS]
   ↳ Latent transformation mask.

- **`63613498`** [COUNTER_LIB, FROZENSET_KEY, STACK_DFS]
   ↳ Latent mask: locate the legend box (region enclosed by an L of color-5

- **`6a1e5592`** [BBOX, FROZENSET_KEY, STACK_DFS]
   ↳ The grid has a top band of color 2 with 0-cells carved into it (each carved

- **`9b4c17c4`** [CONN4_TUPLE, QUEUE_BFS, STACK_DFS]
   ↳ Infer a latent transformation mask.

- **`aa62e3f4`** [BORDER_LOOP, CONN4_TUPLE, QUEUE_BFS]
   ↳ Background cells reachable from the grid border (the outside region).

- **`ac0c5833`** [BBOX, COL_SETTLE, STACK_DFS]
   ↳ 8-connected components of `color` in grid g.

- **`b15fca0b`** [BG_COUNTER, CONN4_TUPLE, QUEUE_BFS]
   ↳ Latent mask: the shortest 4-connected path of background (0) cells

- **`b74ca5d1`** [BG_COUNTER, COUNTER_LIB, FROZENSET_KEY]
   ↳ * Background = most common color.

- **`b782dc8a`** [CONN4_TUPLE, DIAG_RESIDUE, QUEUE_BFS]
   ↳ Non-background, non-wall cells form the seed marker.

- **`b9630600`** [CONN4_TUPLE, CONN8_TUPLE, TUPLE_NORMALIZE]
   ↳ Find axis-aligned hollow rectangles (color 3) as bounding boxes.

- **`d4f3cd78`** [BBOX, BG_COUNTER, RAY_STEP]
   ↳ Infer the latent fill/ray mask.

- **`e5062a87`** [BG_COUNTER, CONN4_TUPLE, FROZENSET_KEY]
   ↳ - The grid is a noise field of foreground (the dominant non-background color

- **`ecb67b6d`** [BG_COUNTER, RAY_STEP, STACK_DFS]
   ↳ The grid contains a background color (the most common color) and a

- **`f3b10344`** [BG_COUNTER, FROZENSET_KEY, STACK_DFS]
   ↳ background of 0. Same-color blocks that face each other (overlap along one axis

- **`18447a8d`** [BG_COUNTER, FROZENSET_KEY]
   ↳ Split rows into bands separated by fully-background rows.

- **`39e1d7f9`** [MAX_BY_LEN, STACK_DFS]
   ↳ Collapse the gridline-separated grid into a coarse cell-grid.

- **`3ed85e70`** [BBOX, STACK_DFS]
   ↳ 8-connected components of non-bg cells restricted to `region` (a set of (r,c)).

- **`4acc7107`** [BBOX, QUEUE_BFS]
   ↳ Connected components (8-connectivity) of non-zero cells, grouped by color.

- **`4c5c2cf0`** [CONN8_TUPLE, FROZENSET_KEY]
   ↳ ----

- **`6d58a25d`** [COUNTER_LIB, STACK_DFS]
   ↳ Infer a latent mask {(r,c): color} of the cells to overwrite.

- **`85fa5666`** [CONN8_TUPLE, RAY_STEP]
   ↳ Locate every 2x2 block of color 2. Return their top-left corners.

- **`b942fd60`** [QUEUE_BFS, RAY_STEP]
   ↳ A single seed cell of color 2 sits on the grid border.  It emits a horizontal

- **`f8f52ecc`** [BG_COUNTER, TUPLE_NORMALIZE]
   ↳ The background color is the most common color.  Color 8 forms wall objects.

- **`fe9372f3`** [CONN4_TUPLE, CONN8_TUPLE]
   ↳ Structure: a plus-shaped marker (color 2, a center cell with one arm in each of

- **`2bee17df`** [ROT90_IDX]
   ↳ ----

- **`5af49b42`** [BORDER_LOOP]
   ↳ Compute the latent stamp mask {(r,c): color}.

- **`67a3c6ac`** [HFLIP_IDX]
   ↳ H, W = len(input_grid), len(input_grid[0])

---

## UNCLUSTERED (no features detected, bigger pile)

- **`045e512c`** ↳ The grid contains one "main" shape (the connected component with the most
- **`05a7bcf2`** ↳ H, W = len(g), len(g[0])
- **`070dd51e`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`09629e4f`** ↳ Infer the latent fill mask.
- **`0a938d79`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`0b17323b`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`0becf7df`** ↳ Read the 2x2 legend at the top-left corner. Each ROW of the legend is a
- **`0d3d703e`** ↳ cmap = {1: 5, 5: 1, 2: 6, 6: 2, 3: 4, 4: 3, 8: 9, 9: 8}
- **`0e671a1a`** ↳ Locate the three colored marker cells (2, 3, 4).
- **`103eff5b`** ↳ ----
- **`12422b43`** ↳ Infer the latent overwrite mask T as {(r,c): color}.
- **`13713586`** ↳ Locate the full row or column of color 5 (the wall).
- **`137f0df0`** ↳ Infer the latent transformation mask.
- **`15113be4`** ↳ Infer the latent mask {(r,c): new_color}.
- **`178fcbfb`** ↳ Infer the latent overwrite mask from marker cells.
- **`17b80ad2`** ↳ Build a latent mask {(r,c): new_color}.
- **`17b866bd`** ↳ Infer the latent transformation mask.
- **`18286ef8`** ↳ The grid is partitioned by full lines of 0 into a 3x3 array of "rooms".
- **`1b60fb0c`** ↳ 180-degree (point) rotationally symmetric. There is a unique center about which
- **`1c02dbbe`** ↳ Latent mask: each marker-color spans a rectangle from its corner anchor
- **`1c0d0a4b`** ↳ Latent mask: dict {(r,c): new_color}.
- **`1e32b0e9`** ↳ Infer the latent transformation mask {(r,c): new_color}.
- **`1f0c79e5`** ↳ Infer the latent transformation mask {(r,c): color}.
- **`1f642eb9`** ↳ Latent mask {(r,c): color}: project each border marker onto the edge
- **`21f83797`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`2204b7a8`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`2281f1f4`** ↳ Infer the latent fill mask.
- **`23581191`** ↳ Latent mask: each marker (8 and 7) projects a full row+column line in its
- **`25094a63`** ↳ Latent mask: every maximal solid monochromatic rectangle of size >= 4x4
- **`253bf280`** ↳ Latent mask: cells strictly between adjacent collinear pairs of 8s
- **`2546ccf6`** ↳ ----
- **`25d8a9c8`** ↳ Latent mask: each cell gets 5 if its row is uniform (all same color),
- **`2685904e`** ↳ Latent transformation mask.
- **`272f95fa`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`27a77e38`** ↳ Infer the latent transformation mask {(r,c): color}.
- **`28e73c20`** ↳ square spiral wall of color 3 starting at the top-left corner (0,0), moving
- **`29623171`** ↳ H, W = len(grid), len(grid[0])
- **`2b01abd0`** ↳ Locate the full-length divider line made of color 1.
- **`2bcee788`** ↳ Infer the latent transformation mask.
- **`2dd70a9a`** ↳ ----
- **`319f2597`** ↳ Infer the latent transformation mask.
- **`31adaf00`** ↳ square block of background (0) cells of side >= 2. Selecting from the largest
- **`32597951`** ↳ Latent mask: inside the bounding box of the 8-marker region,
- **`35ab12c3`** ↳ Cells of the straight/45-diagonal segment a..b, or None if not aligned.
- **`3618c87e`** ↳ Each '1' marker falls straight down its column, dropping below the
- **`3631a71a`** ↳ overwritten with the noise color 9. Reconstruct each 9 cell from the symmetry
- **`363442ee`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`36fdfd69`** ↳ Group the 2-cells by proximity (Chebyshev distance <= 2 links them into one
- **`3906de3d`** ↳ Per-column rule: each vertical bar of 2s rises to stack immediately
- **`3ac3eb23`** ↳ Each nonzero cell in row 0 is a marker of color v at column c.
- **`3bd67248`** ↳ Infer the latent overwrite mask.
- **`3d6c6e23`** ↳ Build a latent transformation mask {(r,c): color}.
- **`3eda0437`** ↳ Return a latent mask: a dict {(r,c): new_color} of cells to overwrite.
- **`3f23242b`** ↳ Build a latent transformation mask {(r,c): color}.
- **`41ace6b5`** ↳ Infer a latent mask {(r,c): new_color} for puzzle 41ace6b5.
- **`423a55dc`** ↳ sheared to the left: each colored cell at row r is shifted LEFT by (maxr - r)
- **`4258a5f9`** ↳ Latent mask: for every cell containing a 5, mark its 8 neighbours
- **`42918530`** ↳ interior), separated by background. Boxes are grouped by their frame color.
- **`42a15761`** ↳ Structure: the grid is split into vertical strips by full all-0 separator
- **`456873bc`** ↳ T = infer_T(input_grid)
- **`45bbe264`** ↳ Each non-zero marker (r,c,color) projects a full-column line and a
- **`4612dd53`** ↳ drawn with color 1 (with gaps). Vertical wall columns are the columns that
- **`470c91de`** ↳ Each colored rectangle is missing one corner cell, which is replaced by an
- **`48634b99`** ↳ Find vertical contiguous runs of non-7 cells, per column.
- **`494ef9d7`** ↳ Latent mask: dict {(r,c): new_color} for cells overwritten by the magnet rule.
- **`4aab4007`** ↳ Structure of every grid:
- **`4cd1b7b2`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`4e45f183`** ↳ ----
- **`508bd3b6`** ↳ Trace the diagonal ray emitted from the 8-line tip; bounce off the 2-wall.
- **`50a16a69`** ↳ The input is a doubly-periodic tile pattern occupying the top-left block,
- **`5168d44c`** ↳ Infer the latent transformation mask for puzzle 5168d44c.
- **`5207a7b5`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`5582e5ca`** ↳ Latent mask: fill the whole grid with the most frequent input color.
- **`575b1a71`** ↳ Latent mask: recolor every 0 by the rank of its column.
- **`58e15b12`** ↳ ----
- **`5a5a2103`** ↳ Infer a latent mask {(r,c): color}.
- **`5b526a93`** ↳ arranged on a lattice. They occupy a set R of distinct top-left rows and a set
- **`5c2c9af4`** ↳ Infer a latent mask of cells to paint as concentric square (Chebyshev)
- **`5e6bbc0b`** ↳ The input is a checkerboard of 1s and 0s with a single 8 sitting on one
- **`626c0bcc`** ↳ bounding box is 2x2. Four piece types occur, each mapped to a fixed color by
- **`62b74c02`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`6350f1f4`** ↳ Structure: the grid is a regular array of equal-size blocks separated by
- **`642248e4`** ↳ Place a border-colored marker one step from each '1' toward the nearer
- **`673ef223`** ↳ Return list of (col, sorted_rows) for each vertical run of 2s on an edge column.
- **`69889d6e`** ↳ that travels toward the upper-right. Each diagonal step paints the leading cell
- **`6a980be1`** ↳ n = len(seq)
- **`6bcdb01e`** ↳ Infer the latent transformation mask for puzzle 6bcdb01e.
- **`6c434453`** ↳ Find every 3x3 hollow square (ring of eight 1s around a 0 center).
- **`6cf79266`** ↳ Latent mask: find every maximal non-overlapping 3x3 region of pure
- **`6d0160f0`** ↳ Infer a latent transformation mask {(r,c): new_color}.
- **`6df30ad6`** ↳ single-cell "noise" pixels in several other colors. The shape is recolored
- **`6e02f1e3`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`6ea4a07e`** ↳ Infer the latent transformation mask from the input alone.
- **`6f8cd79b`** ↳ Latent mask: every perimeter cell becomes color 8 (border frame).
- **`712bf12e`** ↳ Trace a ray upward from each marker (2) on the bottom; the ray climbs
- **`72207abc`** ↳ Infer the latent mask of cells to fill.
- **`72a961c9`** ↳ colored markers (cells that are neither 0 nor 1). From each marker, a
- **`73c3b0d8`** ↳ Locate the solid line of 2s. Returns ('h', row) for a horizontal wall.
- **`74dd1130`** ↳ Latent mask: reflect the grid across its main diagonal (transpose).
- **`758abdf0`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`759f3fd3`** ↳ Infer the latent overwrite mask.
- **`762cd429`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`770cc55f`** ↳ Infer the latent fill mask.
- **`782b5218`** ↳ Infer the recolor mask.
- **`79369cc6`** ↳ ----
- **`7c8af763`** ↳ Infer the latent fill mask.
- **`7d419a02`** ↳ Structure
- **`7e2bad24`** ↳ A diagonal trail of 1s is a ball travelling diagonally. It continues past
- **`7ee1c6ea`** ↳ Infer the latent transformation mask.
- **`817e6c09`** ↳ ----
- **`833966f4`** ↳ Latent mask: for each column, swap rows in consecutive pairs starting
- **`834ec97d`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`8403a5d5`** ↳ Infer the latent overwrite mask {(r,c): color} from input structure.
- **`84551f4c`** ↳ Find vertical bars (single-column nonzero runs): (col, color, height).
- **`855e0971`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`85c4e7cd`** ↳ Concentric square rings: build a mask that recolors each ring with the
- **`891232d6`** ↳ Each cell with color 6 in the grid is a "launcher". From each launcher a
- **`8d510a79`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`8dab14c2`** ↳ The shape is a thick rectangular "pipe" / bent arm of color 1. Its straight walls
- **`8e5a5113`** ↳ Infer overwrite mask. The grid is a row of equal-width square panels
- **`8eb1be9a`** ↳ Latent mask: the input has a contiguous horizontal band of non-empty rows
- **`8ee62060`** ↳ Infer the latent transformation mask.
- **`8f2ea7aa`** ↳ Infer the latent fractal-stamp mask.
- **`903d1b4a`** ↳ Latent transformation mask.
- **`913fb3ed`** ↳ Latent mask: for each non-background marker, the surrounding 3x3 ring
- **`91714a58`** ↳ Find the unique solid filled monochrome rectangle (single nonzero color,
- **`928ad970`** ↳ Infer a latent mask: a hollow rectangle in the box color whose four edges
- **`9356391f`** ↳ Infer the latent overwrite mask {(r,c): color}.
- **`93b581b8`** ↳ Compute a latent transformation mask {(r,c): new_color}.
- **`941d9a10`** ↳ Split indices 0..n-1 into contiguous segments separated by `seps`.
- **`963f59bc`** ↳ Latent mask: stamp a mirrored copy of the 1-shape at each colored marker.
- **`96a8c0cd`** ↳ that travels straight into the grid (perpendicular to the edge it sits on).
- **`97239e3d`** ↳ Infer the latent colouring mask.
- **`97999447`** ↳ For each non-background (non-zero) seed pixel, build a mask that extends
- **`97d7923e`** ↳ H = len(input_grid); W = len(input_grid[0])
- **`98c475bf`** ↳ ----
- **`992798f6`** ↳ Infer the latent mask: a diagonal/straight 'bent line' of color 3 that
- **`9b365c51`** ↳ Left-side legend = single-color full-height vertical bars (not color 8),
- **`9c56f360`** ↳ slides left across background (0) cells until its leading edge is blocked by
- **`9d9215db`** ↳ Non-zero cells live on a 9x9 sub-lattice (grid rows/cols 1,3,5,...,17, i.e.
- **`9ddd00f0`** ↳ Latent mask for a self-similar fractal block grid.
- **`9f41bd9c`** ↳ Infer the latent overwrite mask T (dict {(r,c): new_color}).
- **`9f5f939b`** ↳ Return a latent mask {(r,c): new_color} marking the centers of the
- **`a2fd1cf0`** ↳ Latent mask: cells to paint with 8 forming an L-shaped elbow path that
- **`a3df8b1e`** ↳ Trace a 45-degree ray bouncing off the side walls, starting from the
- **`a3f84088`** ↳ ----
- **`a406ac07`** ↳ Latent mask: for each header color, fill the rectangle that is the
- **`a5f85a15`** ↳ Diagonal chains of colored cells run down-right (successor = (r+1,c+1)).
- **`a61f2674`** ↳ Find connected vertical bars of color 5, return list of (cells, height).
- **`a64e4611`** ↳ The grid is a field of sparse noise tiles separated by blank "corridors".
- **`a65b410d`** ↳ Find the horizontal bar of 2s (left-aligned). Build a mask that, for each
- **`a699fb00`** ↳ Latent mask: for every horizontal pattern 1,0,1, the middle 0 becomes 2.
- **`a78176bb`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`a79310a0`** ↳ Latent transformation mask: clear every 8 from its original cell and
- **`a8d7556c`** ↳ 0-cells whose *smaller* side is exactly 2 (i.e. 2xN or Nx2 strips, where the
- **`aa300dc3`** ↳ ----
- **`ac3e2b04`** ↳ Structure of the puzzle:
- **`ac605cbb`** ↳ ----
- **`ad173014`** ↳ Detect rectangular boxes bordered by color 2; return the colored shape
- **`af22c60d`** ↳ transpose symmetry plus a vertical mirror and a horizontal mirror about
- **`af902bf9`** ↳ Find every axis-aligned rectangle whose 4 corners are color-4 cells with
- **`b1948b0a`** ↳ Latent mask: every cell holding color 6 is recolored to 2.
- **`b60334d2`** ↳ Each 5 marker is the center of a 3x3 stamp: corners stay 5,
- **`b7249182`** ↳ Two colored markers lie on a common row (horizontal pair) or common
- **`b7fb29bc`** ↳ Infer the fill mask for the interior of the 3-bordered rectangle.
- **`b8825c91`** ↳ ground-truth output). The input is partially occluded by a rectangular block of
- **`ba97ae07`** ↳ Two perpendicular colored bands cross. One band ('line') spans the entire
- **`baf41dbf`** ↳ ----
- **`bd4472b8`** ↳ Infer a latent mask: below a separator row, fill each row with a color
- **`bda2d7a6`** ↳ The grid is a set of concentric square rings, each a single color. The
- **`bdad9b1f`** ↳ one made of color 8 and one made of color 2. Each segment lies along a single
- **`bf89d739`** ↳ - The grid contains scattered marker cells of color 2 on a background of 0.
- **`c444b776`** ↳ Structure: the grid is divided into rectangular panels by full lines (rows
- **`c87289bb`** ↳ Structure of the input:
- **`c8f0f002`** ↳ Latent mask: every cell holding the marker color 7 is recolored to 5.
- **`c9f8e694`** ↳ Infer a latent recolor mask.
- **`caa06a1f`** ↳ Structure of every input: a doubly-periodic ("tiled") pattern occupies the
- **`ce039d91`** ↳ left-right mirror axis of the grid, any 5 whose horizontally mirrored partner
- **`ce9e57f2`** ↳ bar, the bottom floor(height/2) cells are recolored to 8; the rest stay 2.
- **`cf133acc`** ↳ Structure of every input:
- **`d037b0a7`** ↳ Infer a latent mask: each 0 cell takes the color of the nearest
- **`d23f8c26`** ↳ on the center column (index W//2) is cleared to background 0, while the center
- **`d2acf2cb`** ↳ column) define a line segment.  The cells strictly between the two markers
- **`d364b489`** ↳ colors in its 4-neighborhood: 7 to the left, 6 to the right, 8 below, 2
- **`d406998b`** ↳ Structure of every pair: a 3-row grid whose only non-zero cells are 5s, with
- **`d492a647`** ↳ Infer a latent transformation mask.
- **`d4a91cb9`** ↳ Infer the latent transformation mask: an L-shaped connector (color 4)
- **`d511f180`** ↳ Infer a latent transformation mask.
- **`d94c3b52`** ↳ Structure: the grid is partitioned into 3x3 cell blocks separated by a single
- **`d9f24cd1`** ↳ - The bottom row contains 2-colored "emitter" markers.
- **`db0c5428`** ↳ Structure: a single 9x9 block sits on a background. The block is a 3x3
- **`db3e9e38`** ↳ Find the vertical 7-line, then emit a diagonal expanding fan of 7/8
- **`db7260a4`** ↳ - A single marker cell of color 1 sits in the top row; it is always removed.
- **`dbc1a6ce`** ↳ markers that share a row or a column, with no other marker lying strictly
- **`dc1df850`** ↳ Infer a latent mask: surround each color-2 marker with a ring of 1s.
- **`dd2401ed`** ↳ Structure of every pair:
- **`e048c9ed`** ↳ * The grid contains a single isolated marker cell of color 5 in the top row;
- **`e179c5f4`** ↳ grid. The ball travels along the long axis of the grid, bouncing off the side
- **`e2092e0c`** ↳ Structure: a marker sits in the top-left 4x4 corner. Its right column (col 3)
- **`e21a174a`** ↳ single color and occupies a contiguous, non-overlapping band of rows. The
- **`e40b9e2f`** ↳ appendage cells.  The output is the 4-fold rotational (C4) closure of the input
- **`e45ef808`** ↳ Structure: row 0 is a constant marker row (all 0). Below it, color-1 fills the
- **`e5790162`** ↳ - The grid contains a single START cell colored 3, some TURN markers
- **`e74e1818`** ↳ Infer a latent transformation mask.
- **`e7b06bea`** ↳ Infer a latent transformation mask {(r,c): new_color}.
- **`e9bb6954`** ↳ - The grid contains one or more solid 3x3 monochromatic blocks (non-zero color).
- **`e9c9d9a1`** ↳ The grid is partitioned into a block matrix by full rows/columns of the
- **`ecdecbb3`** ↳ Structure: full rows/columns of 8 act as walls. Each isolated cell of color 2
- **`ed36ccf7`** ↳ cell at output position (r, c) takes the value of the input cell at
- **`ef26cbf6`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`f0df5ff0`** ↳ Infer the latent transformation mask.
- **`f15e1fac`** ↳ Structure of every pair:
- **`f1cefba8`** ↳ Structure: a rectangular frame (border color) encloses a solid rectangle of a
- **`f35d900a`** ↳ Structure: four single-cell markers sit at the corners of an axis-aligned
- **`f3cdc58f`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`f5c89df1`** ↳ center marker (color 3), plus several position markers (color 2). The template's
- **`f76d97a5`** ↳ H, W = len(input_grid), len(input_grid[0])
- **`f8a8fe49`** ↳ Structure: a rectangular "box" frame of color 2 with two complete parallel
- **`f9a67cb5`** ↳ Structure: the grid contains straight walls made of 8s (either full rows or
- **`f9d67f8b`** ↳ Structure of the task
- **`fcc82909`** ↳ background. For each block, count the number of DISTINCT colors it
- **`ff2825db`** ↳ Structure: a 10x10 grid whose top row (row 0) is a legend, with a solid frame
- **`ff72ca3e`** ↳ Infer latent transformation mask.
