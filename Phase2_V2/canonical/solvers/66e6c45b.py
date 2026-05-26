def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    if not cells:
        return {}
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    rmin, rmax = min(rs), max(rs)
    cmin, cmax = min(cs), max(cs)
    T = {}
    # vacate the central block
    for (r, c) in cells:
        T[(r, c)] = bg
    # fling each colored cell to its corresponding grid corner
    for (r, c) in cells:
        nr = 0 if r <= (rmin + rmax) / 2 else H - 1
        nc = 0 if c <= (cmin + cmax) / 2 else W - 1
        T[(nr, nc)] = input_grid[r][c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
