def infer_T(input_grid):
    """Latent mask: for every cell containing a 5, mark its 8 neighbours
    (within bounds) to be painted with color 1."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 5:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < H and 0 <= nc < W:
                            T[(nr, nc)] = 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
