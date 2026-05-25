def infer_T(input_grid):
    """Find the single non-background marker, then build a mask of the four
    diagonal rays (slopes +/-1) emanating from it out to the grid edges."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    marker = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg:
                marker = (r, c, input_grid[r][c])
    T = {}
    if marker is None:
        return T
    mr, mc, color = marker
    for dr in (-1, 1):
        for dc in (-1, 1):
            r, c = mr, mc
            while 0 <= r < H and 0 <= c < W:
                T[(r, c)] = color
                r += dr
                c += dc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
