def infer_T(input_grid):
    """Infer the latent overwrite mask from the two colored markers.

    Two non-background marker cells appear, one above the other. Each marker
    owns a horizontal band of rows (split at the midpoint between the two
    markers). Within its band, a marker's color fills the left/right column
    borders, a full horizontal line at the marker's own row, and a full
    horizontal line at the band's outer edge (top row for the upper marker,
    bottom row for the lower marker).
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    markers = [(r, c, input_grid[r][c])
               for r in range(H) for c in range(W)
               if input_grid[r][c] != bg]
    markers.sort(key=lambda m: m[0])

    T = [[None] * W for _ in range(H)]
    if len(markers) != 2:
        return T

    (r1, c1, col1), (r2, c2, col2) = markers
    split = (r1 + r2) // 2 + 1  # rows [0, split-1] = top band, [split, H-1] = bottom band

    bands = [
        (0, split - 1, r1, col1, 'top'),
        (split, H - 1, r2, col2, 'bottom'),
    ]
    for top, bot, mrow, col, which in bands:
        # vertical borders of the band
        for r in range(top, bot + 1):
            T[r][0] = col
            T[r][W - 1] = col
        # full horizontal line at the marker's own row
        for c in range(W):
            T[mrow][c] = col
        # full horizontal line at the band's outer edge
        edge = top if which == 'top' else bot
        for c in range(W):
            T[edge][c] = col
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
