from collections import Counter


def infer_T(input_grid):
    """Latent mask: cells whose color is NOT among the two most-frequent
    colors get recolored to 7. Computed from input color histogram alone."""
    H, W = len(input_grid), len(input_grid[0])
    counts = Counter(v for row in input_grid for v in row)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    keep = {ranked[0][0]}
    if len(ranked) > 1:
        keep.add(ranked[1][0])
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] not in keep:
                T[r][c] = 7
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
