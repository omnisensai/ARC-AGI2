from collections import Counter


def infer_T(input_grid):
    """Latent mask: blank everything, draw a 3x3 box of 2s around the cell
    holding the unique non-zero color, keeping that color at the center."""
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter(v for row in input_grid for v in row if v != 0)
    uniques = [k for k, v in cnt.items() if v == 1]
    if len(uniques) != 1:
        return [[None] * W for _ in range(H)]
    target = uniques[0]
    pos = next(((r, c) for r in range(H) for c in range(W)
                if input_grid[r][c] == target), None)
    T = [[0] * W for _ in range(H)]  # overwrite all cells to background
    if pos is None:
        return T
    cr, cc = pos
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            r, c = cr + dr, cc + dc
            if 0 <= r < H and 0 <= c < W:
                T[r][c] = 2
    T[cr][cc] = target
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
