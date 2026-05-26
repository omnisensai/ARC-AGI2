"""Canonical latent-T solver for ARC puzzle e73095fd.

Rule
----
The grid contains a network of straight "wall" lines plus rectangular "boxes"
(closed wall outlines). Every box's hollow interior (a solid rectangle of
background cells) is painted with color 4. Pockets that merely look like boxes
but are really gaps between crossing through-lines (walls protrude past the
box footprint) or open corners (clipped on two grid edges) are NOT filled.

infer_T detects each background rectangle, classifies it as a genuine box, and
records the fill mask. apply_T overwrites only the masked interior cells.
"""

FILL = 4


def _rects(grid, bg):
    """All solid (perfectly rectangular) connected components of color `bg`."""
    H, W = len(grid), len(grid[0])
    seen = set()
    res = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg and (r, c) not in seen:
                comp = []
                st = [(r, c)]
                while st:
                    rr, cc = st.pop()
                    if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W) or grid[rr][cc] != bg:
                        continue
                    seen.add((rr, cc))
                    comp.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        st.append((rr + dr, cc + dc))
                rs = [x[0] for x in comp]
                cs = [x[1] for x in comp]
                r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
                if len(comp) == (r1 - r0 + 1) * (c1 - c0 + 1):
                    res.append((r0, r1, c0, c1))
    return res


def _is_box(grid, wall, r0, r1, c0, c1):
    """True iff the background rectangle [r0..r1]x[c0..c1] is a closed box.

    A closed box is wrapped by a `wall`-colored ring. Each side must be either a
    solid wall or entirely off-grid (clipped by the grid edge, at most one such
    side). The ring corners must seal (wall or off-grid), and no wall may
    protrude beyond the box footprint (which would mark a crossing through-line
    rather than a box).
    """
    H, W = len(grid), len(grid[0])

    def v(r, c):
        if 0 <= r < H and 0 <= c < W:
            return grid[r][c]
        return None  # off-grid

    sides = [
        [(r0 - 1, c) for c in range(c0, c1 + 1)],   # top
        [(r1 + 1, c) for c in range(c0, c1 + 1)],   # bottom
        [(r, c0 - 1) for r in range(r0, r1 + 1)],   # left
        [(r, c1 + 1) for r in range(r0, r1 + 1)],   # right
    ]
    clipped = 0
    for cells in sides:
        vals = [v(r, c) for r, c in cells]
        if all(x == wall for x in vals):
            continue
        if all(x is None for x in vals):
            clipped += 1
            continue
        return False
    if clipped > 1:
        return False

    for cr, cc in ((r0 - 1, c0 - 1), (r0 - 1, c1 + 1), (r1 + 1, c0 - 1), (r1 + 1, c1 + 1)):
        if v(cr, cc) not in (wall, None):
            return False

    beyond = (
        (r0 - 2, c0 - 1), (r0 - 2, c1 + 1), (r1 + 2, c0 - 1), (r1 + 2, c1 + 1),
        (r0 - 1, c0 - 2), (r1 + 1, c0 - 2), (r0 - 1, c1 + 2), (r1 + 1, c1 + 2),
    )
    for cr, cc in beyond:
        if v(cr, cc) == wall:
            return False
    return True


def infer_T(input_grid):
    """Latent transformation mask: interiors of closed boxes -> FILL, else None."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for x in row:
            counts[x] = counts.get(x, 0) + 1
    bg = max(counts, key=counts.get)
    wall = max((k for k in counts if k != bg), key=counts.get, default=None)

    T = [[None] * W for _ in range(H)]
    if wall is None:
        return T
    for (r0, r1, c0, c1) in _rects(input_grid, bg):
        if _is_box(input_grid, wall, r0, r1, c0, c1):
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    T[r][c] = FILL
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
