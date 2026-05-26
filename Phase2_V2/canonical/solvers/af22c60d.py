"""Canonical solver for ARC puzzle af22c60d.

Rule: the grid is a fully symmetric texture (it obeys a main-diagonal
transpose symmetry plus a vertical mirror and a horizontal mirror about
off-center axes). Some cells have been blanked out with the noise color 0.
The transformation restores every blanked cell from its symmetric
counterpart(s), so the output is the original symmetric grid with the holes
filled in.

infer_T: discover the symmetry maps obeyed by all the non-zero cells, then
build a mask {(r,c): color} for every 0-cell, propagating colors across the
symmetry group until no hole can be filled.
apply_T: copy the input and overwrite only the masked (formerly 0) cells.
"""

NOISE = 0


def _candidate_maps(H, W):
    """All elementary symmetry maps to test as generators.

    Each map is (name, fn) where fn(r, c) -> (r2, c2). Mirror axes are tried
    at every position; transpose / anti-transpose only when square.
    """
    maps = []
    # Vertical mirrors: c -> k - c  (reflection across some column axis)
    for k in range(2 * W - 1):
        maps.append(("vmir%d" % k, (lambda k: (lambda r, c: (r, k - c)))(k)))
    # Horizontal mirrors: r -> k - r
    for k in range(2 * H - 1):
        maps.append(("hmir%d" % k, (lambda k: (lambda r, c: (k - r, c)))(k)))
    if H == W:
        maps.append(("transpose", lambda r, c: (c, r)))
        maps.append(("anti", lambda r, c: (W - 1 - c, H - 1 - r)))
    return maps


def _map_consistent(grid, fn, H, W, min_pairs=20):
    """A map is accepted if every cell pair it relates (both non-noise and in
    bounds) agrees in color, and it relates a meaningful number of pairs."""
    pairs = 0
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v == NOISE:
                continue
            rr, cc = fn(r, c)
            if not (0 <= rr < H and 0 <= cc < W):
                continue
            w = grid[rr][cc]
            if w == NOISE:
                continue
            if w != v:
                return False, 0
            pairs += 1
    return (pairs >= min_pairs), pairs


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # Discover the symmetry maps obeyed by the visible (non-noise) cells.
    good = []
    for _name, fn in _candidate_maps(H, W):
        ok, _ = _map_consistent(input_grid, fn, H, W)
        if ok:
            good.append(fn)

    # Build the repair mask by propagating known colors through the symmetry
    # maps until no more holes can be resolved.
    filled = [row[:] for row in input_grid]
    changed = True
    while changed:
        changed = False
        for r in range(H):
            for c in range(W):
                if filled[r][c] != NOISE:
                    continue
                for fn in good:
                    rr, cc = fn(r, c)
                    if 0 <= rr < H and 0 <= cc < W and filled[rr][cc] != NOISE:
                        filled[r][c] = filled[rr][cc]
                        changed = True
                        break

    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == NOISE and filled[r][c] != NOISE:
                T[(r, c)] = filled[r][c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
