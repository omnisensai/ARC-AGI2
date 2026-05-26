def infer_T(input_grid):
    """Infer the latent overwrite mask from seed pixels.

    Each non-background seed decorates its neighborhood:
      - color 1 -> place 7 at the 4 orthogonal neighbors
      - color 2 -> place 4 at the 4 diagonal neighbors
    Other colors (e.g. 8, 6) are inert seeds and add nothing.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    ORTHO = ((-1, 0), (1, 0), (0, -1), (0, 1))
    DIAG = ((-1, -1), (-1, 1), (1, -1), (1, 1))
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == 1:
                for dr, dc in ORTHO:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W:
                        T[(nr, nc)] = 7
            elif v == 2:
                for dr, dc in DIAG:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W:
                        T[(nr, nc)] = 4
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
