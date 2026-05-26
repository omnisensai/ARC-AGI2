"""Canonical latent-T solver for ARC puzzle 11852cab.

Rule: the non-background figure lives in a SQUARE bounding box and is meant to
have full dihedral (D4) symmetry of that square -- horizontal mirror, vertical
mirror, both diagonal mirrors and the 90-degree rotations. The input is a
partially-drawn version of this symmetric figure. infer_T computes, for every
background cell inside the bounding box, the color implied by the consensus of
its D4 symmetry orbit; apply_T overwrites only those cells.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = 0
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    T = {}
    if not cells:
        return T
    rmin = min(r for r, c in cells); rmax = max(r for r, c in cells)
    cmin = min(c for r, c in cells); cmax = max(c for r, c in cells)
    n = rmax - rmin  # span of the (square) bounding box

    def orbit(r, c):
        lr, lc = r - rmin, c - cmin
        pts = set()
        for (a, b) in [(lr, lc), (lr, n - lc), (n - lr, lc), (n - lr, n - lc),
                       (lc, lr), (lc, n - lr), (n - lc, lr), (n - lc, n - lr)]:
            pts.add((rmin + a, cmin + b))
        return pts

    for r in range(rmin, rmax + 1):
        for c in range(cmin, cmax + 1):
            if input_grid[r][c] != bg:
                continue
            vals = [input_grid[gr][gc] for gr, gc in orbit(r, c)
                    if input_grid[gr][gc] != bg]
            if not vals:
                continue
            T[(r, c)] = max(set(vals), key=vals.count)
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
