"""Canonical solver for ARC puzzle 6ca952ad.

Rule: the grid holds several connected objects (4-connectivity) of a single
non-background color on a background of 7. Each object is classified by shape:

  - A "block" object occupies at least 2 columns that each span 2 or more rows
    (i.e. it is genuinely two-dimensional, not a thin line / L-stub). Every
    block falls straight down with its columns and shape preserved until its
    bottom row lands on the last grid row.
  - A "thin marker" object (everything else: single cells, vertical/horizontal
    lines, and small L-stubs that have only one tall column) stays in place.

The latent mask vacates each faller's original cells (sets them to background)
and paints the faller's color at the dropped-down cells.

The column-span test is what distinguishes train pair 0's staying L-stub
(##/.# -> only one column has 2 cells) from blocks that look superficially
similar but have 2+ tall columns.
"""


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _components(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] == bg:
                        continue
                    seen.add((a, b))
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    """Return a latent mask grid of None/int describing every changed cell."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    T = [[None] * W for _ in range(H)]
    clears = set()
    placements = {}
    for cells in _components(input_grid, bg):
        colcount = {}
        for r, c in cells:
            colcount[c] = colcount.get(c, 0) + 1
        tall_cols = sum(1 for c in colcount if colcount[c] >= 2)
        color = input_grid[cells[0][0]][cells[0][1]]
        if tall_cols >= 2:  # block -> falls to the bottom
            bottom = max(r for r, _ in cells)
            shift = (H - 1) - bottom
            for r, c in cells:
                clears.add((r, c))
            for r, c in cells:
                placements[(r + shift, c)] = color
        # else: thin marker -> stays in place
    for (r, c) in clears:
        T[r][c] = bg
    for (r, c), color in placements.items():
        T[r][c] = color
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
