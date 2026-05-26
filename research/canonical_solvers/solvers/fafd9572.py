"""Canonical solver for ARC puzzle fafd9572.

Structure:
  - A small "legend" object made of colors other than 0 (background) and 1
    (shape color). It is a single connected component and its bounding box,
    read as a sub-grid, gives a 2D arrangement of target colors (0 = empty).
  - Several "shapes" drawn in color 1. The shapes are laid out on the grid in
    a regular row/column arrangement that mirrors the legend's arrangement.

Rule: recolor each shape (all its 1-cells) to the legend color occupying the
matching cell of the legend's grid. The shape grid is recovered by binning the
shape bounding-box centers into rows and columns and matching index-by-index
against the non-empty rows/columns of the legend.
"""


def _components(grid, pred):
    H, W = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if (r, c) in seen or not pred(grid[r][c]):
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                a, b = stack.pop()
                if (a, b) in seen or not (0 <= a < H and 0 <= b < W) or not pred(grid[a][b]):
                    continue
                seen.add((a, b))
                cells.append((a, b))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    stack.append((a + dr, b + dc))
            out.append(cells)
    return out


def _bin_coords(values, tol=1):
    """Group sorted distinct centroid coordinates into bands; return a function
    mapping a value to its band index, plus the number of bands."""
    uniq = sorted(set(values))
    bands = []  # list of representative coords
    for v in uniq:
        if bands and v - bands[-1] <= tol:
            continue
        bands.append(v)
    # assign each value to nearest band index
    def band_index(v):
        best = 0
        bestd = None
        for i, b in enumerate(bands):
            d = abs(v - b)
            if bestd is None or d < bestd:
                bestd = d
                best = i
        return best
    return band_index, len(bands)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # legend: connected component(s) of colors not in {bg, 1}
    legend_cells = _components(input_grid, lambda v: v != bg and v != 1)
    T = {}
    if not legend_cells:
        return T
    # the legend is the largest such component (others, if any, are noise)
    legend = max(legend_cells, key=len)

    lr0 = min(r for r, c in legend)
    lr1 = max(r for r, c in legend)
    lc0 = min(c for r, c in legend)
    lc1 = max(c for r, c in legend)

    # legend sub-grid of colors (bg -> 0 meaning "empty")
    leg_grid = []
    for r in range(lr0, lr1 + 1):
        leg_grid.append([input_grid[r][c] for c in range(lc0, lc1 + 1)])
    LH = len(leg_grid)
    LW = len(leg_grid[0])

    # which legend rows / cols are non-empty
    leg_rows = [i for i in range(LH) if any(leg_grid[i][j] != bg for j in range(LW))]
    leg_cols = [j for j in range(LW) if any(leg_grid[i][j] != bg for i in range(LH))]

    # shapes: connected components of color 1
    shapes = _components(input_grid, lambda v: v == 1)
    if not shapes:
        return T

    # centroid of each shape
    centers = []
    for cells in shapes:
        cr = sum(r for r, c in cells) / len(cells)
        cc = sum(c for r, c in cells) / len(cells)
        centers.append((cr, cc))

    row_index, nrows = _bin_coords([cr for cr, cc in centers], tol=2)
    col_index, ncols = _bin_coords([cc for cr, cc in centers], tol=2)

    # map shape band index -> legend non-empty row/col index
    def map_band(idx, n_shape_bands, leg_nonempty):
        if n_shape_bands == len(leg_nonempty):
            return leg_nonempty[idx]
        # fallback: proportional
        if n_shape_bands <= 1:
            return leg_nonempty[0]
        pos = int(round(idx * (len(leg_nonempty) - 1) / (n_shape_bands - 1)))
        return leg_nonempty[pos]

    for cells, (cr, cc) in zip(shapes, centers):
        ri = row_index(cr)
        ci = col_index(cc)
        lr = map_band(ri, nrows, leg_rows)
        lc = map_band(ci, ncols, leg_cols)
        color = leg_grid[lr][lc]
        if color == bg:
            continue
        for (r, c) in cells:
            T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
