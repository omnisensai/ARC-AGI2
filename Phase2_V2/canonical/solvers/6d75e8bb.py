def infer_T(input_grid):
    """Fill the background (0) cells inside the bounding box of the 8-shape with 2."""
    H, W = len(input_grid), len(input_grid[0])
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]
    if not cells:
        return {}
    rmin = min(r for r, c in cells)
    rmax = max(r for r, c in cells)
    cmin = min(c for r, c in cells)
    cmax = max(c for r, c in cells)
    T = {}
    for r in range(rmin, rmax + 1):
        for c in range(cmin, cmax + 1):
            if input_grid[r][c] == 0:
                T[(r, c)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
