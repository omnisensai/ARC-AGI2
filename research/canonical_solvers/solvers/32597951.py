def infer_T(input_grid):
    """Latent mask: inside the bounding box of the 8-marker region,
    every background-pattern cell that is 1 gets recolored to 3.
    The 8 cells and the 0 cells are left untouched."""
    H, W = len(input_grid), len(input_grid[0])
    # locate marker cells (color 8)
    marks = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]
    T = {}
    if not marks:
        return T
    rs = [r for r, c in marks]
    cs = [c for r, c in marks]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if input_grid[r][c] == 1:
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
