def infer_T(input_grid):
    """Latent mask: every 0-cell whose 4 orthogonal neighbors are all 0 is a
    plus-center; that center and its four arms get recolored to 3."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0:
                continue
            nb = [(r + dr, c + dc) for dr, dc in dirs]
            if all(0 <= nr < H and 0 <= nc < W and input_grid[nr][nc] == 0
                   for nr, nc in nb):
                T[r][c] = 3
                for nr, nc in nb:
                    T[nr][nc] = 3
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
