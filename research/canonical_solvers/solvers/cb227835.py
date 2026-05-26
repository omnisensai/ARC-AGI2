"""Canonical solver for ARC puzzle cb227835.

Rule: the grid contains two marker cells of one color (8). Connect them with a
thin parallelogram "tube" drawn in color 3. The tube is two L-shaped rails
between the two markers: each rail consists of a 45-degree diagonal segment of
length S = min(|dr|,|dc|) and a straight segment of length L-S = |long axis|-S.
One rail does diagonal-then-straight, the other straight-then-diagonal, so they
form the two sides of a parallelogram whose acute corners are the markers. The
marker cells themselves are left untouched.
"""


def _sign(x):
    return (x > 0) - (x < 0)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Background = most common color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Marker cells = all non-background cells (the two 8s).
    markers = [(r, c) for r in range(H) for c in range(W)
               if input_grid[r][c] != bg]

    T = {}  # latent mask: {(r,c): new_color}
    if len(markers) != 2:
        return T

    a, b = markers[0], markers[1]
    dr, dc = b[0] - a[0], b[1] - a[1]
    sr, sc = _sign(dr), _sign(dc)
    L = max(abs(dr), abs(dc))
    S = min(abs(dr), abs(dc))
    horiz = abs(dc) >= abs(dr)  # dominant axis is horizontal

    fill_color = 3

    def trace(diag_first):
        cur = a
        segs = [('d', S), ('s', L - S)] if diag_first else [('s', L - S), ('d', S)]
        path = []
        for kind, n in segs:
            for _ in range(n):
                if kind == 'd':
                    cur = (cur[0] + sr, cur[1] + sc)
                elif horiz:
                    cur = (cur[0], cur[1] + sc)
                else:
                    cur = (cur[0] + sr, cur[1])
                path.append(cur)
        return path

    for cell in trace(True) + trace(False):
        if cell == a or cell == b:
            continue
        r, c = cell
        if 0 <= r < H and 0 <= c < W and input_grid[r][c] == bg:
            T[cell] = fill_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
