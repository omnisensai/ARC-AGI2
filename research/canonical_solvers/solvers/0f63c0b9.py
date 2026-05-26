def infer_T(input_grid):
    """Infer the latent transformation mask {(r,c): color}.

    Structure: the grid contains several single-cell colored markers on a
    background of 0. Each marker's row defines a horizontal band; bands are
    split at the midpoints between adjacent markers (sorted by row). Within a
    band, the left and right edge columns are painted with the band color, the
    marker's own row becomes a full horizontal line, and if the band touches
    the top or bottom edge of the grid that edge row is also a full line.
    """
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # collect markers (single non-bg cells)
    markers = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg:
                markers.append((r, input_grid[r][c]))
    markers.sort()

    T = {}
    n = len(markers)
    for i, (mr, color) in enumerate(markers):
        top = 0 if i == 0 else (markers[i - 1][0] + mr) // 2 + 1
        bottom = H - 1 if i == n - 1 else (mr + markers[i + 1][0]) // 2
        for r in range(top, bottom + 1):
            # determine which rows in this band are full horizontal lines
            full = (r == mr) or (r == 0 and top == 0) or (r == H - 1 and bottom == H - 1)
            if full:
                for c in range(W):
                    T[(r, c)] = color
            else:
                T[(r, 0)] = color
                T[(r, W - 1)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
