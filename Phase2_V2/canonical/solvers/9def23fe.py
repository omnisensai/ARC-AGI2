"""Canonical solver for ARC puzzle 9def23fe.

Rule
----
The grid contains one solid rectangle of color 2 and a scatter of single-cell
markers of one other color (3 / 8 / 4 / 1 depending on the pair).

For each of the four sides of the rectangle, look at the markers lying on that
side (above / below = markers sharing a column with the rect; left / right =
markers sharing a row with the rect). Each marker "uses up" the rectangle line
(column for above/below, row for left/right) it is aligned with. Every
rectangle line on that side that is NOT claimed by a marker gets projected
outward as a full line of 2s, from the rectangle edge all the way to the grid
border on that side.

So the projected comb on each side is exactly the complement of the marker
positions on that side. A side with no markers projects every line (a full
fan), while lines hit by a marker leave a gap.
"""

from collections import Counter


def infer_T(input_grid):
    """Compute the latent mask of cells to overwrite with 2."""
    H = len(input_grid)
    W = len(input_grid[0])

    counts = Counter(v for row in input_grid for v in row)
    bg = counts.most_common(1)[0][0]

    # Bounding box of the color-2 rectangle.
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 2]
    if not cells:
        return {}
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)

    # Marker colors: anything that is neither background nor the rectangle color.
    marker_colors = set(v for row in input_grid for v in row if v != bg and v != 2)

    def side(r, c):
        if r < r0:
            return "above"
        if r > r1:
            return "below"
        if c < c0:
            return "left"
        if c > c1:
            return "right"
        return "inside"

    T = {}
    for mc in marker_colors:
        markers = [(r, c) for r in range(H) for c in range(W)
                   if input_grid[r][c] == mc]
        above = set(c for r, c in markers if side(r, c) == "above")
        below = set(c for r, c in markers if side(r, c) == "below")
        left = set(r for r, c in markers if side(r, c) == "left")
        right = set(r for r, c in markers if side(r, c) == "right")

        # Project unclaimed columns up / down.
        for c in range(c0, c1 + 1):
            if c not in above:
                for r in range(0, r0):
                    T[(r, c)] = 2
            if c not in below:
                for r in range(r1 + 1, H):
                    T[(r, c)] = 2
        # Project unclaimed rows left / right.
        for r in range(r0, r1 + 1):
            if r not in left:
                for c in range(0, c0):
                    T[(r, c)] = 2
            if r not in right:
                for c in range(c1 + 1, W):
                    T[(r, c)] = 2

    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
