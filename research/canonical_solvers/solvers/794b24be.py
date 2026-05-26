def infer_T(input_grid):
    """Infer the latent transformation mask.

    The non-background cells are merely counted (their positions are
    irrelevant). The number N of non-background cells determines how far a
    fixed drawing order is filled with color 2; every other cell is cleared to
    background. So T overwrites the ENTIRE grid: background everywhere except
    the first N cells of the fixed order, which become 2.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    n = sum(1 for row in input_grid for v in row if v != bg)

    # Fixed fill order observed across all pairs.
    order = [(0, 0), (0, 1), (0, 2), (1, 1)]
    draw = set()
    for i in range(min(n, len(order))):
        r, c = order[i]
        if 0 <= r < H and 0 <= c < W:
            draw.add((r, c))

    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            T[r][c] = 2 if (r, c) in draw else bg
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
