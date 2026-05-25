"""Canonical solver for ARC puzzle 3631a71a.

Rule: the grid is a symmetric mosaic in which a rectangular patch has been
overwritten with the noise color 9. Reconstruct each 9 cell from the symmetry
group of the rest of the grid. The grid is invariant (ignoring 9s) under the
main-diagonal transpose and under mirror reflections about a half-integer
row/column axis. infer_T discovers which candidate symmetries actually hold on
the visible (non-9) cells, takes their group closure, and for every 9 cell
looks up a non-9 partner in its symmetry orbit. apply_T overwrites only the
masked (9) cells with the recovered colors.
"""

NOISE = 9


def _candidate_symmetries(grid):
    """Return the list of point maps (r,c)->(r2,c2) that the visible cells obey.

    Candidates: transpose / anti-transpose about either diagonal, and mirror
    reflections about every half-integer or integer row/column axis. A map is
    accepted only if it has no contradiction on non-noise cells and actually
    relates a substantial number of cells.
    """
    H = len(grid)
    W = len(grid[0])

    def holds(mapfn):
        good = 0
        for r in range(H):
            for c in range(W):
                r2, c2 = mapfn(r, c)
                if not (0 <= r2 < H and 0 <= c2 < W):
                    continue
                a = grid[r][c]
                b = grid[r2][c2]
                if a == NOISE or b == NOISE:
                    continue
                if a != b:
                    return None
                good += 1
        return good

    cands = []

    def consider(mapfn):
        g = holds(mapfn)
        if g is not None and g >= 2 * max(H, W):
            cands.append(mapfn)

    # transpose family (only meaningful when square)
    if H == W:
        consider(lambda r, c: (c, r))
        consider(lambda r, c: (W - 1 - c, H - 1 - r))

    # mirror about a vertical axis at column position ax/2 (covers integer and
    # half-integer axes): c -> ax - c
    for ax in range(0, 2 * W - 1):
        consider((lambda ax: (lambda r, c: (r, ax - c)))(ax))
    # mirror about a horizontal axis at row position ax/2: r -> ax - r
    for ax in range(0, 2 * H - 1):
        consider((lambda ax: (lambda r, c: (ax - r, c)))(ax))

    return cands


def _closure(maps, H, W):
    """Group closure of the given generator maps (plus identity)."""
    def key(f):
        return tuple(f(r, c) for r in range(H) for c in range(W))

    identity = lambda r, c: (r, c)
    seen = {key(identity): identity}
    funcs = [identity]
    changed = True
    while changed:
        changed = False
        new = []
        for f in funcs:
            for g in maps:
                h = (lambda f, g: (lambda r, c: g(*f(r, c))))(f, g)
                k = key(h)
                if k not in seen:
                    seen[k] = h
                    new.append(h)
                    changed = True
        funcs += new
    return list(seen.values())


def infer_T(input_grid):
    """Compute the repair mask: {(r,c): recovered_color} for every noise cell."""
    H = len(input_grid)
    W = len(input_grid[0])
    gens = _candidate_symmetries(input_grid)
    group = _closure(gens, H, W)

    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != NOISE:
                continue
            val = None
            for f in group:
                r2, c2 = f(r, c)
                if 0 <= r2 < H and 0 <= c2 < W and input_grid[r2][c2] != NOISE:
                    val = input_grid[r2][c2]
                    break
            if val is not None:
                T[(r, c)] = val
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
