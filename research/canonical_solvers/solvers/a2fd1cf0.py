def infer_T(input_grid):
    """Latent mask: cells to paint with 8 forming an L-shaped elbow path that
    connects the 2 marker and the 3 marker. The horizontal arm runs along the
    2's row, the vertical arm runs along the 3's column; they meet at the corner
    (row-of-2, col-of-3). Endpoint marker cells are not overwritten."""
    H, W = len(input_grid), len(input_grid[0])
    pos = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v in (2, 3):
                pos[v] = (r, c)
    T = {}
    if 2 not in pos or 3 not in pos:
        return T
    r2, c2 = pos[2]
    r3, c3 = pos[3]
    corner = (r2, c3)  # elbow at 2's row, 3's column

    def paint(cells):
        for (r, c) in cells:
            if (r, c) in (pos[2], pos[3]):
                continue
            T[(r, c)] = 8

    # horizontal arm along 2's row, from c2 to c3 (corner column)
    lo, hi = sorted((c2, c3))
    paint((r2, c) for c in range(lo, hi + 1))
    # vertical arm along 3's column, from r2 (corner row) to r3
    lo, hi = sorted((r2, r3))
    paint((r, c3) for r in range(lo, hi + 1))
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
