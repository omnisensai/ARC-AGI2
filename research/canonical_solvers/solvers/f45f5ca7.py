def infer_T(input_grid):
    """Each colored cell sits in column 0 of its row. It is shifted right to a
    column determined solely by its color (a fixed per-color offset). The
    transformation mask records, for every colored source cell, that its
    original cell becomes background (0) and the destination cell takes the
    color."""
    H, W = len(input_grid), len(input_grid[0])

    # Per-color destination column (fixed semantic property of each color).
    color_col = {8: 1, 2: 2, 4: 3, 3: 4}

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    T = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg:
                continue
            if v in color_col:
                dest = color_col[v]
                if 0 <= dest < W:
                    T[(r, c)] = bg      # clear the source cell
                    T[(r, dest)] = v    # place color at destination column
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
