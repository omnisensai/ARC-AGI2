def infer_T(input_grid):
    """Locate the single marker (color 2) and compute the latent change mask.

    The marker is cleared to background (0) and each of its four diagonal
    neighbours that lies inside the grid is painted with a fixed color:
        up-left = 3, up-right = 6, down-left = 8, down-right = 7.
    """
    H, W = len(input_grid), len(input_grid[0])
    src = next(((r, c) for r in range(H) for c in range(W)
                if input_grid[r][c] == 2), None)
    T = {}
    if src is None:
        return T
    r, c = src
    T[(r, c)] = 0
    diag = {(-1, -1): 3, (-1, 1): 6, (1, -1): 8, (1, 1): 7}
    for (dr, dc), col in diag.items():
        nr, nc = r + dr, c + dc
        if 0 <= nr < H and 0 <= nc < W:
            T[(nr, nc)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
