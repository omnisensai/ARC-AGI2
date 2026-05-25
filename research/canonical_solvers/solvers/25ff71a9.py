def infer_T(input_grid):
    """Latent mask: shift the entire grid down by one row.
    For each target cell (r,c), the new value comes from the cell directly
    above it (r-1,c); the new top row is filled with the background color.
    Returns a dict {(r,c): new_color} covering every cell."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    T = {}
    for r in range(H):
        for c in range(W):
            src_r = r - 1
            if 0 <= src_r < H:
                T[(r, c)] = input_grid[src_r][c]
            else:
                T[(r, c)] = bg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
