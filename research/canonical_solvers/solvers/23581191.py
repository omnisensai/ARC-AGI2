def infer_T(input_grid):
    """Latent mask: each marker (8 and 7) projects a full row+column line in its
    own color; cells where an 8-line crosses a 7-line become 2."""
    H, W = len(input_grid), len(input_grid[0])
    pos = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v in (8, 7):
                pos[v] = (r, c)
    T = {}
    if 8 not in pos or 7 not in pos:
        return T
    r8, c8 = pos[8]
    r7, c7 = pos[7]
    # 7's cross
    for c in range(W):
        T[(r7, c)] = 7
    for r in range(H):
        T[(r, c7)] = 7
    # 8's cross (overwrites 7 on plain crossings)
    for c in range(W):
        T[(r8, c)] = 8
    for r in range(H):
        T[(r, c8)] = 8
    # 8-line x 7-line intersections become 2
    T[(r8, c7)] = 2
    T[(r7, c8)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
