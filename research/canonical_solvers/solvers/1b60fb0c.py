"""Canonical solver for ARC puzzle 1b60fb0c.

Rule: the input holds a single figure drawn in color 1 that is *almost*
180-degree (point) rotationally symmetric. There is a unique center about which
reflecting the figure stays in bounds and overlaps the existing figure maximally.
Reflecting every 1-cell about that center yields the existing cells plus a set of
"missing" cells needed to complete the point symmetry. Those missing cells are
filled with color 2.

Canonical latent-T form: infer_T builds a mask {(r,c): 2} of the cells that must
be filled to complete the rotational symmetry; apply_T overwrites only those.
"""


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    ones = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 1]
    ones_set = set(ones)

    # Search every candidate 180-degree center (indexed in doubled coordinates so
    # half-integer centers are representable). A valid center reflects the whole
    # figure back in bounds; among those choose the center maximizing overlap with
    # the existing figure (i.e. the figure is as point-symmetric as possible).
    best = None  # (overlap, (tr, tc))
    for tr in range(0, 2 * H):
        for tc in range(0, 2 * W):
            in_bounds = True
            overlap = 0
            for (r, c) in ones:
                rr, cc = tr - r, tc - c
                if not (0 <= rr < H and 0 <= cc < W):
                    in_bounds = False
                    break
                if (rr, cc) in ones_set:
                    overlap += 1
            if not in_bounds:
                continue
            if best is None or overlap > best[0]:
                best = (overlap, (tr, tc))

    T = {}
    if best is None:
        return T
    tr, tc = best[1]
    for (r, c) in ones:
        rr, cc = tr - r, tc - c
        if input_grid[rr][cc] == 0:
            T[(rr, cc)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
