def infer_T(input_grid):
    """Latent mask: paint a grid lattice over background cells.

    Cells lying on an even row or an even column become part of the lattice
    (color 1); cells at odd-row & odd-column intersections stay as the
    background. The mask is computed purely from grid geometry.
    """
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg:
                continue
            if r % 2 == 0 or c % 2 == 0:
                T[r][c] = 1
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
