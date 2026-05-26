"""Canonical solver for ARC puzzle 8dab14c2.

Rule (same-size, color 1 shapes on background 8):
The shape is a thick rectangular "pipe" / bent arm of color 1. Its straight walls
carry small defects:
  * a BUMP  -- a single 1-cell protruding outward from an otherwise flat wall,
               with background on both perpendicular sides.
  * a NOTCH -- a single missing (background) cell denting inward into a flat wall,
               with the wall continuing on both perpendicular sides.
Each defect is reflected across the arm to the OPPOSITE parallel wall, swapping
its polarity: a bump becomes a notch on the far wall, a notch becomes a bump just
beyond the far wall, aligned at the same position along the arm. The original
defect is left untouched. Defects are reflected by ray-casting straight inward
(skipping over single-cell notches in the path) until the opposite wall is found.

infer_T builds the latent change mask {(r,c): new_color}; apply_T overwrites only
those cells on a copy of the input.
"""

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _inb(g, r, c):
    return 0 <= r < len(g) and 0 <= c < len(g[0])


def _get(g, r, c):
    return g[r][c] if _inb(g, r, c) else 8


def _far_wall(g, r, c, dr, dc):
    """Ray-cast inward (opposite the outward defect direction) until the opposite
    wall of the arm is reached, stepping over single-cell notches en route."""
    ir, ic = -dr, -dc
    rr, cc = r, c
    while True:
        nr, nc = rr + ir, cc + ic
        if _get(g, nr, nc) == 1:
            rr, cc = nr, nc
        elif _get(g, nr + ir, nc + ic) == 1:  # single-cell notch in the path
            rr, cc = nr + ir, nc + ic
        else:
            break
    return rr, cc


def _detect(g):
    """Find boundary defects. Returns (bumps, notches) as lists of (r, c, dr, dc),
    where (dr, dc) is the outward direction of the defect."""
    H, W = len(g), len(g[0])
    bumps, notches = [], []
    for r in range(H):
        for c in range(W):
            v = g[r][c]
            for (dr, dc) in DIRS:
                out = _get(g, r + dr, c + dc)
                opp = _get(g, r - dr, c - dc)
                pr1 = _get(g, r + dc, c + dr)
                pr2 = _get(g, r - dc, c - dr)
                if v == 1 and out == 8 and opp == 1 and pr1 == 8 and pr2 == 8:
                    # isolated single-cell protrusion off a wall
                    bumps.append((r, c, dr, dc))
                if v == 8 and out == 8 and opp == 1 and pr1 == 1 and pr2 == 1:
                    # dent in a FLAT wall: outward diagonals bg, inward diagonals fill
                    od1 = _get(g, r + dr + dc, c + dc + dr)
                    od2 = _get(g, r + dr - dc, c + dc - dr)
                    id1 = _get(g, r - dr + dc, c - dc + dr)
                    id2 = _get(g, r - dr - dc, c - dc - dr)
                    if od1 == 8 and od2 == 8 and id1 == 1 and id2 == 1:
                        notches.append((r, c, dr, dc))
    return bumps, notches


def infer_T(input_grid):
    """Latent transformation mask: dict {(r, c): new_color} of cells to overwrite."""
    g = input_grid
    bumps, notches = _detect(g)
    nset = {(r, c) for r, c, _, _ in notches}
    T = {}
    # notch -> bump on the far wall (just beyond it), same position along the arm
    for r, c, dr, dc in notches:
        wr, wc = _far_wall(g, r, c, dr, dc)
        T[(wr - dr, wc - dc)] = 1
    # bump -> notch on the far wall. Skip bumps that are merely the corner created
    # by an adjacent notch (those are not independent defects).
    for r, c, dr, dc in bumps:
        if any((r + a, c + b) in nset for a in (-1, 0, 1) for b in (-1, 0, 1)):
            continue
        wr, wc = _far_wall(g, r, c, dr, dc)
        T[(wr, wc)] = 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if _inb(input_grid, r, c):
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
