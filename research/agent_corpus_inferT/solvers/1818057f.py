def infer_T(input_grid):
    """Infer the transformation mask: every plus/cross of the foreground color
    (a 4-cell whose 4 orthogonal neighbors are all 4) is recolored to 8.
    Returns a dict {(r,c): new_value}.
    """
    H, W = len(input_grid), len(input_grid[0])
    FG = 4
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != FG:
                continue
            neigh = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
            if all(0 <= nr < H and 0 <= nc < W and input_grid[nr][nc] == FG
                   for nr, nc in neigh):
                T[(r, c)] = 8
                for nr, nc in neigh:
                    T[(nr, nc)] = 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
