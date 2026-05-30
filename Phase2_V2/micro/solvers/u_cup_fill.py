from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = [(r, c, g[r][c]) for r in range(H) for c in range(W) if g[r][c] != bg]
    # marker = rarest non-bg colour (a single isolated cell)
    counts = Counter(v for _, _, v in nz)
    marker_col = min(counts, key=lambda k: counts[k])
    cup_cells = [(r, c) for r, c, v in nz if v != marker_col]
    if not cup_cells:
        return {}
    cup_col = next(v for _, _, v in nz if v != marker_col)
    top = min(r for r, c in cup_cells); bottom = max(r for r, c in cup_cells)
    left = min(c for r, c in cup_cells); right = max(c for r, c in cup_cells)
    T = {}
    for r in range(top, bottom):              # above the floor row
        for c in range(left + 1, right):      # between the walls
            if g[r][c] == bg:
                T[(r, c)] = marker_col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
