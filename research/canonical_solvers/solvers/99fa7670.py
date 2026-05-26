def infer_T(input_grid):
    """Build a latent mask {(r,c): color} drawing, for each marker cell, an
    L-shaped path: horizontal from the marker to the right edge, then vertical
    down the last column until the row of the next-lower marker (exclusive) or
    the bottom edge."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    markers = [(r, c, input_grid[r][c])
               for r in range(H) for c in range(W)
               if input_grid[r][c] != bg]
    markers.sort()

    T = {}
    for i, (r, c, col) in enumerate(markers):
        # horizontal arm: marker to right edge
        for cc in range(c, W):
            T[(r, cc)] = col
        # vertical arm: down the last column until next-lower marker row
        next_row = H
        for j in range(i + 1, len(markers)):
            if markers[j][0] > r:
                next_row = markers[j][0]
                break
        for rr in range(r + 1, min(next_row, H)):
            T[(rr, W - 1)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
