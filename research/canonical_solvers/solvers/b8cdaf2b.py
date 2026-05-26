def infer_T(input_grid):
    """Latent mask: the two diagonal rays of the core color emanating from the
    top-left and top-right corners of the structure, going up-and-outward until
    they leave the grid."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # core color = color of the bottom-center cell of the structure
    core = input_grid[H - 1][W // 2]
    # topmost non-background row of the structure
    top = None
    for r in range(H):
        if any(input_grid[r][c] != bg for c in range(W)):
            top = r
            break
    T = {}
    if top is None:
        return T
    cols = [c for c in range(W) if input_grid[top][c] != bg]
    left_c, right_c = cols[0], cols[-1]
    # left ray: diagonally up-left from above the left corner
    r, c = top - 1, left_c - 1
    while 0 <= r < H and 0 <= c < W:
        T[(r, c)] = core
        r -= 1
        c -= 1
    # right ray: diagonally up-right from above the right corner
    r, c = top - 1, right_c + 1
    while 0 <= r < H and 0 <= c < W:
        T[(r, c)] = core
        r -= 1
        c += 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
