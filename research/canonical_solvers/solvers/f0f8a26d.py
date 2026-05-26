"""Canonical ARC solver for puzzle f0f8a26d.

Rule: the grid contains straight line segments (connected components, all
horizontal or vertical) drawn on a uniform background. Each segment is rotated
90 degrees about its own midpoint (the center of its bounding box). A horizontal
bar becomes a vertical bar through the same center, and vice versa. The latent
transformation T records, for every cell, the color it must hold after the
rotation: original segment cells are cleared to background and the rotated
target cells receive the segment color.
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
                    x, y = stack.pop()
                    if (x, y) in seen or not (0 <= x < H and 0 <= y < W):
                        continue
                    if grid[x][y] == bg:
                        continue
                    seen.add((x, y))
                    cells.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((x + dx, y + dy))
                comps.append(sorted(cells))
    return comps


def infer_T(input_grid):
    """Compute the latent transformation mask as {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    clears = set()
    sets = {}
    for cells in _components(input_grid, bg):
        color = input_grid[cells[0][0]][cells[0][1]]
        rows = [c[0] for c in cells]
        cols = [c[1] for c in cells]
        # center of the segment's bounding box (its midpoint)
        cr = (min(rows) + max(rows)) / 2.0
        cc = (min(cols) + max(cols)) / 2.0
        # original cells are candidates to be cleared to background
        for r, c in cells:
            clears.add((r, c))
        # rotate 90 degrees about the center: (r,c) -> (cr + (c-cc), cc - (r-cr))
        for r, c in cells:
            nr = int(round(cr + (c - cc)))
            nc = int(round(cc - (r - cr)))
            if 0 <= nr < H and 0 <= nc < W:
                sets[(nr, nc)] = color
    # build the mask: clears first, then rotated colors win on overlap
    T = {}
    for cell in clears:
        T[cell] = bg
    for cell, color in sets.items():
        T[cell] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
