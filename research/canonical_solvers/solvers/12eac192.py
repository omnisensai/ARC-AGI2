"""Canonical solver for ARC puzzle 12eac192.

Rule (derived from ALL pairs):
Background is color 0. For every non-background cell, group cells into
orthogonally-connected, single-color components. Any component whose size is
small (< 3 cells) is "noise" and gets recolored to 3; components of size >= 3
are real shapes and are left untouched. Background (0) is never changed.

infer_T builds the latent mask of cells to recolor; apply_T overwrites them.
"""


def _components(grid, color, H, W):
    """Orthogonally-connected single-color components of `color`."""
    seen = set()
    out = []
    nb = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cell = []
                while stack:
                    x, y = stack.pop()
                    if (x, y) in seen or not (0 <= x < H and 0 <= y < W):
                        continue
                    if grid[x][y] != color:
                        continue
                    seen.add((x, y))
                    cell.append((x, y))
                    for dr, dc in nb:
                        stack.append((x + dr, y + dc))
                out.append(cell)
    return out


def infer_T(input_grid):
    """Latent mask: dict {(r,c): 3} for every cell in a small (size<3) component."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    T = {}
    colors = {input_grid[r][c] for r in range(H) for c in range(W)} - {bg}
    for color in colors:
        for cell in _components(input_grid, color, H, W):
            if len(cell) < 3:
                for (r, c) in cell:
                    T[(r, c)] = 3
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
