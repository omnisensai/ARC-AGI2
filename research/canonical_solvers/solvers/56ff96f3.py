def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # group non-background cells by color
    cells_by_color = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg:
                continue
            cells_by_color.setdefault(v, []).append((r, c))
    # latent mask: fill each color's bounding box with that color
    T = {}
    for color, cells in cells_by_color.items():
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
