def infer_T(input_grid):
    """Latent transformation mask: clear every 8 from its original cell and
    re-place the whole shape one row down, recolored to 2."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    src = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]
    for (r, c) in src:
        T[(r, c)] = 0              # clear original cell
    for (r, c) in src:
        nr = r + 1
        if 0 <= nr < H:
            T[(nr, c)] = 2         # placement (recolored) overrides clears
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
