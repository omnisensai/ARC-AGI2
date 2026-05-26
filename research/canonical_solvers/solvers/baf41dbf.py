"""Canonical solver for ARC puzzle baf41dbf.

Rule
----
The input contains one box (color 3) shaped as a grid of rooms: a rectangular
region whose full horizontal rows and full vertical columns of 3s are "walls".
Scattered around the box are 6 markers, each lying outside the box on one of its
sides. Every marker stretches the box so that the OUTERMOST wall on that side
moves out to sit immediately next to the marker (one cell short of it). Interior
walls keep their positions; only the outer wall on the pulled side moves, so the
outermost room is enlarged while inner rooms stay the same. Markers themselves
are left in place.

A corner marker may be aligned with neither the original rows nor columns; it is
classified after other markers stretch the box enough to make it row/col aligned
(handled by the iterative classification in infer_T).

Latent T: a 2D None/int mask. infer_T computes the new box (cleared old cells set
to 0, rebuilt walls set to 3); apply_T overwrites only those masked cells.
"""


def _box_bounds(g):
    H, W = len(g), len(g[0])
    rs = [r for r in range(H) for c in range(W) if g[r][c] == 3]
    cs = [c for r in range(H) for c in range(W) if g[r][c] == 3]
    return min(rs), max(rs), min(cs), max(cs)


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    T = [[None] * W for _ in range(H)]

    # no box -> nothing to do
    if not any(g[r][c] == 3 for r in range(H) for c in range(W)):
        return T

    r0, r1, c0, c1 = _box_bounds(g)

    # interior wall lines (full rows / full columns of 3 within the box)
    hwall = [r for r in range(r0, r1 + 1)
             if all(g[r][c] == 3 for c in range(c0, c1 + 1))]
    vwall = [c for c in range(c0, c1 + 1)
             if all(g[r][c] == 3 for r in range(r0, r1 + 1))]

    markers = [(r, c) for r in range(H) for c in range(W) if g[r][c] == 6]

    # iteratively classify markers and stretch the bounds.
    nr0, nr1, nc0, nc1 = r0, r1, c0, c1
    pending = list(markers)
    changed = True
    while pending and changed:
        changed = False
        still = []
        for (mr, mc) in pending:
            rowin = nr0 <= mr <= nr1
            colin = nc0 <= mc <= nc1
            if rowin and not colin:          # left / right stretch
                if mc < nc0:
                    nc0 = mc + 1
                elif mc > nc1:
                    nc1 = mc - 1
                changed = True
            elif colin and not rowin:        # up / down stretch
                if mr < nr0:
                    nr0 = mr + 1
                elif mr > nr1:
                    nr1 = mr - 1
                changed = True
            else:
                still.append((mr, mc))
        pending = still

    # new wall positions: only the outer walls move with the new bounds
    nh = [nr0 if h == r0 else (nr1 if h == r1 else h) for h in hwall]
    nv = [nc0 if v == c0 else (nc1 if v == c1 else v) for v in vwall]

    # clear every old 3 cell
    for r in range(H):
        for c in range(W):
            if g[r][c] == 3:
                T[r][c] = 0

    # draw the rebuilt box walls
    nh_set, nv_set = set(nh), set(nv)
    for r in range(nr0, nr1 + 1):
        for c in range(nc0, nc1 + 1):
            if r in nh_set or c in nv_set:
                T[r][c] = 3
            elif g[r][c] == 3:
                T[r][c] = 0

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for r in range(len(out)):
        for c in range(len(out[0])):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
