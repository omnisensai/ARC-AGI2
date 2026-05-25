"""Canonical latent-T solver for ARC puzzle 50f325b5.

Rule
----
The grid contains one small "key" object drawn in color 8 (an 8-connected
polyomino). Scattered elsewhere in the noisy grid are copies of that same
polyomino drawn in color 3 (every cell of the copy is a 3). Each such copy is
recolored from 3 to 8.

A copy may appear under any of the polyomino's rotations or (for chiral
shapes) reflections. Rotated placements take priority: a reflected placement is
only accepted when it does not overlap a placement already accepted from the
rotation orientations. This resolves the rare case where a rotated copy and a
reflected copy share cells -- the rotated (un-flipped) reading wins.

The latent transformation T is the dict {(r, c): 8} of all cells belonging to
accepted copies; apply_T overwrites only those cells.
"""


def _normset(cells):
    """Translate a set of cells so its bounding box starts at (0, 0)."""
    mr = min(r for r, c in cells)
    mc = min(c for r, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _rotation_orients(shape):
    """The distinct normalized orientations reachable by rotation only."""
    res, seen = [], set()
    cur = set(shape)
    for _ in range(4):
        n = _normset(cur)
        if n not in seen:
            seen.add(n)
            res.append(sorted(n))
        cur = {(c, -r) for r, c in cur}  # rotate 90 degrees
    return res


def _reflection_orients(shape):
    """Normalized orientations from reflecting then rotating, excluding any
    that are already reachable by rotation alone."""
    rot = {frozenset(o) for o in _rotation_orients(shape)}
    res, seen = [], set()
    cur = {(r, -c) for r, c in shape}  # reflect across vertical axis
    for _ in range(4):
        n = _normset(cur)
        if n not in rot and n not in seen:
            seen.add(n)
            res.append(sorted(n))
        cur = {(c, -r) for r, c in cur}
    return res


def _placements(input_grid, orients):
    """All in-bounds placements of the given orientations whose every cell
    is color 3, returned as frozensets of absolute coordinates."""
    H, W = len(input_grid), len(input_grid[0])
    found = []
    for orient in orients:
        oh = max(r for r, c in orient) + 1
        ow = max(c for r, c in orient) + 1
        for r0 in range(H - oh + 1):
            for c0 in range(W - ow + 1):
                cells = [(r0 + r, c0 + c) for r, c in orient]
                if all(input_grid[r][c] == 3 for r, c in cells):
                    found.append(frozenset(cells))
    return found


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    template = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]
    T = {}
    if not template:
        return T

    rot_pl = _placements(input_grid, _rotation_orients(template))
    ref_pl = _placements(input_grid, _reflection_orients(template))

    # Greedily accept non-overlapping copies, rotations before reflections.
    used = set()
    for pl in rot_pl + ref_pl:
        if pl & used:
            continue
        used |= pl
        for cell in pl:
            T[cell] = 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
