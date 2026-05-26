def infer_T(input_grid):
    """Infer a latent transformation mask.

    Structure: exactly two marker cells of the same non-background color lie
    on a common axis (same row or same column). A plus/cross is drawn (color 3)
    centered at the midpoint between the two markers.
    """
    H, W = len(input_grid), len(input_grid[0])

    # background = most frequent color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # collect non-background marker cells
    markers = [(r, c) for r in range(H) for c in range(W)
               if input_grid[r][c] != bg]

    T = {}
    if len(markers) != 2:
        return T

    (r0, c0), (r1, c1) = markers
    # midpoint (markers share a row or a column -> integer midpoint)
    mr = (r0 + r1) // 2
    mc = (c0 + c1) // 2

    plus = [(mr, mc), (mr - 1, mc), (mr + 1, mc), (mr, mc - 1), (mr, mc + 1)]
    for (r, c) in plus:
        if 0 <= r < H and 0 <= c < W:
            T[(r, c)] = 3
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
