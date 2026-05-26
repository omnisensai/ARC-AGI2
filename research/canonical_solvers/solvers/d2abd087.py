"""Canonical solver for ARC puzzle d2abd087.

Rule: each 8-connected component of color-5 cells is recolored. A component
whose size (cell count) equals 6 becomes color 2; every other component
becomes color 1. Background (0) is unchanged.
"""


def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cur = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] != color:
                        continue
                    seen.add((a, b))
                    cur.append((a, b))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((a + dr, b + dc))
                comps.append(cur)
    return comps


def infer_T(input_grid):
    """Compute latent transformation mask {(r, c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for comp in _components(input_grid, 5):
        new_color = 2 if len(comp) == 6 else 1
        for (r, c) in comp:
            T[(r, c)] = new_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
