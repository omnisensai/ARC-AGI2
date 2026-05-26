def infer_T(input_grid):
    """Latent mask: for each row whose left-edge and right-edge markers are the
    same non-background color, mark the whole row to be filled with that color."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        left = input_grid[r][0]
        right = input_grid[r][W - 1]
        if left != bg and left == right:
            for c in range(W):
                T[r][c] = left
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
