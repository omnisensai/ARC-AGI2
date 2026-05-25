"""Canonical solver for ARC puzzle 1478ab18.

Rule
----
The grid (background 7) holds four marker cells of color 5. Exactly one pair of
markers lies on a shared diagonal (main r-c=const or anti r+c=const); that pair
is the hypotenuse of a right triangle whose right-angle corner is one of the two
remaining corners of the markers' bounding box. The correct corner is the one for
which a THIRD marker (5) lies strictly inside the resulting triangle (on the
corner side of the hypotenuse). The triangle outline -- the two legs along the
corner's row/column plus the diagonal hypotenuse -- is painted with color 8,
leaving the marker (5) cells untouched.
"""


def _bg(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _triangle_cells(E1, E2, corner):
    """Return the set of outline cells of the right triangle with hypotenuse
    E1-E2 and right angle at `corner`, or None if `corner` is not a valid
    right-angle corner for this hypotenuse."""
    if E1[0] == E2[0] or E1[1] == E2[1]:
        return None
    cr, cc = corner
    erow = E1 if E1[0] == cr else E2   # endpoint sharing corner's row
    ecol = E1 if E1[1] == cc else E2   # endpoint sharing corner's column
    if erow[0] != cr or ecol[1] != cc:
        return None
    cells = set()
    c0, c1 = sorted((cc, erow[1]))
    for c in range(c0, c1 + 1):
        cells.add((cr, c))
    r0, r1 = sorted((cr, ecol[0]))
    for r in range(r0, r1 + 1):
        cells.add((r, cc))
    dr = 1 if E2[0] > E1[0] else -1
    dc = 1 if E2[1] > E1[1] else -1
    r, c = E1
    while (r, c) != E2:
        cells.add((r, c))
        r += dr
        c += dc
    cells.add(E2)
    return cells


def infer_T(input_grid):
    """Compute the latent transformation mask: {(r,c): 8} for triangle outline."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg(input_grid)
    marks = [(r, c) for r in range(H) for c in range(W)
             if input_grid[r][c] != bg]
    mset = set(marks)
    T = {}
    for a in range(len(marks)):
        for b in range(a + 1, len(marks)):
            E1, E2 = marks[a], marks[b]
            (r1, c1), (r2, c2) = E1, E2
            main = (r1 - c1 == r2 - c2)
            anti = (r1 + c1 == r2 + c2)
            if not (main or anti):
                continue
            rmin, rmax = min(r1, r2), max(r1, r2)
            cmin, cmax = min(c1, c2), max(c1, c2)
            corners = [(rmin, cmin), (rmin, cmax), (rmax, cmin), (rmax, cmax)]
            for corner in corners:
                tc = _triangle_cells(E1, E2, corner)
                if tc is None:
                    continue
                # require a third marker strictly inside, on the corner side
                inside = False
                for (orr, occ) in (mset - {E1, E2}):
                    if not (rmin <= orr <= rmax and cmin <= occ <= cmax):
                        continue
                    if (orr, occ) in tc:
                        continue
                    if main:
                        k = r1 - c1
                        cs = (corner[0] - corner[1]) - k
                        ps = (orr - occ) - k
                    else:
                        k = r1 + c1
                        cs = (corner[0] + corner[1]) - k
                        ps = (orr + occ) - k
                    if cs * ps > 0:
                        inside = True
                        break
                if inside:
                    for cell in tc:
                        if cell not in mset:
                            T[cell] = 8
                    return T
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
