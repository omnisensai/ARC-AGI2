"""Canonical solver for ARC puzzle 18286ef8.

Rule:
  The grid is partitioned by full lines of 0 into a 3x3 array of "rooms".
  The center room holds a 3x3 block of 5s with a single 9 at its center.
  Exactly one peripheral room contains a marker colored 6.
  The 6's room, relative to the center room (by band index), gives a
  direction (dr, dc) in {-1,0,1}^2. The 9 inside the block moves from the
  block center to (center + (dr, dc)) -- pointing toward that room -- and
  the 6 marker itself is recolored to 9.

infer_T builds the change mask; apply_T overwrites only those cells.
"""


def _sign(x):
    return (x > 0) - (x < 0)


def _bands(grid, axis):
    """Return [(start,end)] of non-separator bands along an axis.

    A separator is a full line of color 0. axis 0 -> rows, axis 1 -> cols.
    """
    H, W = len(grid), len(grid[0])
    n = H if axis == 0 else W
    seps = []
    for i in range(n):
        if axis == 0:
            line = grid[i]
        else:
            line = [grid[r][i] for r in range(H)]
        if all(v == 0 for v in line):
            seps.append(i)
    bands = []
    prev = 0
    for s in seps + [n]:
        if s > prev:
            bands.append((prev, s - 1))
        prev = s + 1
    return bands


def _band_index(bands, x):
    for k, (a, b) in enumerate(bands):
        if a <= x <= b:
            return k
    return None


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    nine = None
    six = None
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == 9:
                nine = (r, c)
            elif v == 6:
                six = (r, c)
    T = {}
    if nine is None or six is None:
        return T

    rb = _bands(input_grid, 0)
    cb = _bands(input_grid, 1)

    nr, nc = _band_index(rb, nine[0]), _band_index(cb, nine[1])
    sr, sc = _band_index(rb, six[0]), _band_index(cb, six[1])
    if None in (nr, nc, sr, sc):
        return T

    dr = _sign(sr - nr)
    dc = _sign(sc - nc)

    target = (nine[0] + dr, nine[1] + dc)

    # restore the old 9 position inside the block to 5
    T[nine] = 5
    # move the 9 to the directional cell of the block
    T[target] = 9
    # recolor the pointed-to 6 marker to 9
    T[six] = 9
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
