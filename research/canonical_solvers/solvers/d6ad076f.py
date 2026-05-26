"""Canonical solver for ARC puzzle d6ad076f.

Two solid colored rectangles sit on a background, separated by a gap along one
axis (either horizontally or vertically). The transformation draws an 8-colored
"bridge" filling the gap between the two rectangles. Along the separation axis
the bridge spans the full empty gap between the rectangles' facing edges. Along
the perpendicular axis the bridge covers the overlap of the two rectangles'
projections, inset (shrunk) by one cell on each side.

Latent T form: infer_T computes a sparse mask {(r,c): 8} for the bridge cells;
apply_T copies the input and overwrites only those cells.
"""

FILL = 8


def _components(grid):
    """Return list of (color, rmin, rmax, cmin, cmax) for each non-background color.

    Background is the most frequent color. Each remaining color forms one solid
    rectangle in this task, so a bounding box per color is sufficient.
    """
    H, W = len(grid), len(grid[0])
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    cells = {}
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v == bg:
                continue
            cells.setdefault(v, []).append((r, c))

    boxes = []
    for color, pts in cells.items():
        rs = [p[0] for p in pts]
        cs = [p[1] for p in pts]
        boxes.append((color, min(rs), max(rs), min(cs), max(cs)))
    return boxes


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    T = {}

    boxes = _components(input_grid)
    if len(boxes) != 2:
        return T

    (_, ar0, ar1, ac0, ac1), (_, br0, br1, bc0, bc1) = boxes

    # Determine separation axis: do the column ranges or the row ranges leave a gap?
    horizontal_gap = (ac1 < bc0) or (bc1 < ac0)
    vertical_gap = (ar1 < br0) or (br1 < ar0)

    if horizontal_gap and not vertical_gap:
        # Bridge runs horizontally; gap columns between the two boxes.
        if ac1 < bc0:
            gc0, gc1 = ac1 + 1, bc0 - 1
        else:
            gc0, gc1 = bc1 + 1, ac0 - 1
        # Perpendicular (row) extent = overlap of row projections, inset by 1.
        o0, o1 = max(ar0, br0), min(ar1, br1)
        gr0, gr1 = o0 + 1, o1 - 1
        rng_r = range(gr0, gr1 + 1)
        rng_c = range(gc0, gc1 + 1)
    elif vertical_gap and not horizontal_gap:
        # Bridge runs vertically; gap rows between the two boxes.
        if ar1 < br0:
            gr0, gr1 = ar1 + 1, br0 - 1
        else:
            gr0, gr1 = br1 + 1, ar0 - 1
        # Perpendicular (column) extent = overlap of column projections, inset by 1.
        o0, o1 = max(ac0, bc0), min(ac1, bc1)
        gc0, gc1 = o0 + 1, o1 - 1
        rng_r = range(gr0, gr1 + 1)
        rng_c = range(gc0, gc1 + 1)
    else:
        return T

    for r in rng_r:
        if not (0 <= r < H):
            continue
        for c in rng_c:
            if not (0 <= c < W):
                continue
            T[(r, c)] = FILL
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
