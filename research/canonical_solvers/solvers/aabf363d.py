def infer_T(input_grid):
    """Recolor the multi-cell shape with the lone marker color; clear the marker.

    The grid has a background, one connected shape (a color appearing >1 time)
    and a single isolated marker cell (a unique color appearing exactly once).
    The latent mask T paints every shape cell with the marker color and resets
    the marker cell to background.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    singles = [v for v, n in counts.items() if v != bg and n == 1]
    shape_colors = [v for v, n in counts.items() if v != bg and n > 1]
    T = {}
    if len(singles) == 1 and len(shape_colors) == 1:
        marker = singles[0]
        shape = shape_colors[0]
        for r in range(H):
            for c in range(W):
                if input_grid[r][c] == shape:
                    T[(r, c)] = marker
                elif input_grid[r][c] == marker:
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
