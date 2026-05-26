def infer_T(input_grid):
    """Latent mask: point-reflect every non-background cell 180 deg about the
    pivot cell (the unique cell colored 5). Background = most common color (0).
    T maps target cell -> new color; background-only cells are cleared to bg."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    pivot = next(((r, c) for r in range(H) for c in range(W)
                  if input_grid[r][c] == 5), None)
    if pivot is None:
        return {}
    pr, pc = pivot

    T = {}
    # First clear every currently-colored cell (it will move away).
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg:
                T[(r, c)] = bg
    # Then place each colored cell at its 180-deg reflection about the pivot.
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg:
                continue
            nr, nc = 2 * pr - r, 2 * pc - c
            if 0 <= nr < H and 0 <= nc < W:
                T[(nr, nc)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
