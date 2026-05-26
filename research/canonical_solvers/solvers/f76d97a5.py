def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    # The grid has two colors: marker color 5 and one other color X.
    # Identify the non-5 color present (the background/shape color).
    others = [c for c in counts if c != 5]
    other = others[0] if others else 5
    T = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == 5:
                T[(r, c)] = other   # marker cells take the other color
            else:
                T[(r, c)] = 0       # other-color cells become 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
