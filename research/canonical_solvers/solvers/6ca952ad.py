"""Canonical solver for ARC puzzle 6ca952ad.

Rule: the grid contains several connected objects (8-connectivity) of a single
non-background color on a background of 7. Objects whose bounding box is a
single column (width == 1) are left untouched. Every object whose bounding box
spans two or more columns is dropped straight down (columns preserved, shape
preserved) so that its bottom row lands on the last grid row. The latent
transformation mask records, for the moved objects, which cells become empty
(their original locations) and which cells become colored (their dropped
locations).
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
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((a + dr, b + dc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    """Return a dict {(r, c): new_color} describing every cell that changes."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    T = {}
    for cells in _components(input_grid, bg):
        cols = [c for _, c in cells]
        width = max(cols) - min(cols) + 1
        if width < 2:
            continue  # single-column objects stay put
        color = input_grid[cells[0][0]][cells[0][1]]
        bottom = max(r for r, _ in cells)
        shift = (H - 1) - bottom  # drop so bottom row hits last grid row
        # vacate the original cells
        for (r, c) in cells:
            T[(r, c)] = bg
        # paint the dropped cells (overrides any vacate at the same spot)
        for (r, c) in cells:
            T[(r + shift, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
