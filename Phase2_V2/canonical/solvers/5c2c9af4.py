def infer_T(input_grid):
    """Infer a latent mask of cells to paint as concentric square (Chebyshev)
    rings.

    The input contains three collinear single-cell markers of one color on a
    background of 0. They lie on a diagonal: the middle marker is the common
    center, and the two outer markers are opposite corners of the innermost
    square ring. The Chebyshev distance from the center to a corner is the
    spacing 'step'. We draw concentric square rings centered at the center at
    radii 0, step, 2*step, ... clipped to the grid.

    Returns (T, color) where T is a set of (r, c) cells to paint.
    """
    H, W = len(input_grid), len(input_grid[0])

    markers = [(r, c) for r in range(H) for c in range(W)
               if input_grid[r][c] != 0]
    if not markers:
        return set(), None
    color = input_grid[markers[0][0]][markers[0][1]]

    # Center = marker minimizing the max Chebyshev distance to the others
    # (for three collinear markers this is the geometric middle one).
    def cheb(a, b):
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

    center = min(markers,
                 key=lambda m: max(cheb(m, o) for o in markers))
    cx, cy = center

    # step = Chebyshev distance from center to the nearest other marker.
    others = [m for m in markers if m != center]
    step = min(cheb(center, o) for o in others) if others else 1
    if step <= 0:
        step = 1

    T = set()
    max_rad = max(cx, H - 1 - cx, cy, W - 1 - cy)
    rad = 0
    while rad <= max_rad:
        r0, r1 = max(0, cx - rad), min(H - 1, cx + rad)
        c0, c1 = max(0, cy - rad), min(W - 1, cy + rad)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if max(abs(r - cx), abs(c - cy)) == rad:
                    T.add((r, c))
        rad += step
    return T, color


def apply_T(input_grid, T_color):
    T, color = T_color
    out = [row[:] for row in input_grid]
    if color is None:
        return out
    for r, c in T:
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
