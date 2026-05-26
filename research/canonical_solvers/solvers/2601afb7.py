def infer_T(input_grid):
    """Build a latent transformation mask {(r,c): new_color}.

    Structure: each non-background column holds a vertical bar (one color,
    some height) anchored to the bottom of the grid. Reading the bars
    left-to-right, the colors rotate RIGHT by one (last -> first) and the
    lengths rotate LEFT by one (first -> last). Each bar is redrawn at its
    column, bottom-anchored, with the rotated color and length.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    # Determine background as the most frequent color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get) if counts else 0

    # Extract bars per occupied column: (col, color, length).
    bars = []
    for c in range(W):
        cells = [r for r in range(H) if input_grid[r][c] != bg]
        if cells:
            color = input_grid[cells[0]][c]
            bars.append((c, color, len(cells)))

    T = {}
    n = len(bars)
    if n == 0:
        return T, bg, H

    colors = [b[1] for b in bars]
    lengths = [b[2] for b in bars]

    # colors rotate right by 1, lengths rotate left by 1.
    rot_colors = [colors[-1]] + colors[:-1]
    rot_lengths = lengths[1:] + [lengths[0]]

    # First clear every old bar cell, then draw new bottom-anchored bars.
    for (c, _color, length) in bars:
        for r in range(H - length, H):
            T[(r, c)] = bg

    for i, (c, _color, _length) in enumerate(bars):
        new_color = rot_colors[i]
        new_len = rot_lengths[i]
        for r in range(H - new_len, H):
            T[(r, c)] = new_color

    return T, bg, H


def apply_T(input_grid, T_bundle):
    T, _bg, _H = T_bundle
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
