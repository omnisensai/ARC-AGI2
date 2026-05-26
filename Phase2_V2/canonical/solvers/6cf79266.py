def infer_T(input_grid):
    """Latent mask: find every maximal non-overlapping 3x3 region of pure
    background (0), scanning top-to-bottom / left-to-right, and mark those
    cells to be recolored to 1."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    used = [[False] * W for _ in range(H)]
    for r in range(H - 2):
        for c in range(W - 2):
            if any(used[r + dr][c + dc] for dr in range(3) for dc in range(3)):
                continue
            if all(input_grid[r + dr][c + dc] == 0
                   for dr in range(3) for dc in range(3)):
                for dr in range(3):
                    for dc in range(3):
                        used[r + dr][c + dc] = True
                        T[r + dr][c + dc] = 1
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
