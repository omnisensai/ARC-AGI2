def _legend(grid):
    """Left-side legend = single-color full-height vertical bars (not color 8),
    read left-to-right (columns 1,3,5,...)."""
    H, W = len(grid), len(grid[0])
    colors = []
    for c in range(W):
        nz = set(grid[r][c] for r in range(H)) - {0}
        if len(nz) == 1 and 8 not in nz:
            colors.append(next(iter(nz)))
    return colors


def _rectangles(grid):
    """Decompose all color-8 cells into maximal solid rectangles.
    Greedy top-left scan: at each unclaimed 8-corner take full row width,
    then grow downward while the full width stays filled."""
    H, W = len(grid), len(grid[0])
    occ = [[grid[r][c] == 8 for c in range(W)] for r in range(H)]
    rects = []
    for r in range(H):
        for c in range(W):
            if not occ[r][c]:
                continue
            w = 0
            while c + w < W and occ[r][c + w]:
                w += 1
            h = 1
            while r + h < H and all(occ[r + h][c + k] for k in range(w)):
                h += 1
            rects.append((r, c, h, w))
            for dr in range(h):
                for dc in range(w):
                    occ[r + dr][c + dc] = False
    return rects


def infer_T(input_grid):
    """Latent mask: erase the legend bars, then recolor each 8-rectangle
    (ordered left-to-right) with the corresponding legend color (top-to-bottom
    = left-to-right). Returns dict {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    legend = _legend(input_grid)
    rects = sorted(_rectangles(input_grid), key=lambda t: (t[1], t[0]))

    T = {}
    # erase every non-background cell that is part of a legend bar
    for c in range(W):
        nz = set(input_grid[r][c] for r in range(H)) - {0}
        if len(nz) == 1 and 8 not in nz:
            for r in range(H):
                if input_grid[r][c] != 0:
                    T[(r, c)] = 0
    # recolor each rectangle in left-to-right order using legend order
    for i, (r, c, h, w) in enumerate(rects):
        color = legend[i] if i < len(legend) else 8
        for dr in range(h):
            for dc in range(w):
                T[(r + dr, c + dc)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
