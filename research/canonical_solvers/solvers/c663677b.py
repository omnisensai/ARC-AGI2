"""Canonical solver for ARC puzzle c663677b.

The grid is a doubly-periodic (tiled) pattern with rectangular holes punched
out using color 0. The transformation restores each hole cell to the value of
the underlying periodic pattern.

infer_T: detect the smallest row period and column period of the pattern
(ignoring holes), build a consensus value for every residue class
(r % pr, c % pc) from the non-hole cells, and mark each hole cell with its
consensus value. apply_T overwrites only those marked cells.
"""

HOLE = 0


def _find_period(grid, axis):
    H = len(grid)
    W = len(grid[0])
    if axis == 1:  # column (horizontal) period
        for p in range(1, W):
            ok = True
            for r in range(H):
                for c in range(p, W):
                    v1 = grid[r][c]
                    v2 = grid[r][c - p]
                    if v1 != HOLE and v2 != HOLE and v1 != v2:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                return p
        return W
    else:  # row (vertical) period
        for p in range(1, H):
            ok = True
            for r in range(p, H):
                for c in range(W):
                    v1 = grid[r][c]
                    v2 = grid[r - p][c]
                    if v1 != HOLE and v2 != HOLE and v1 != v2:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                return p
        return H


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    pr = _find_period(input_grid, 0)
    pc = _find_period(input_grid, 1)

    # Consensus non-hole value for each residue class.
    counts = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == HOLE:
                continue
            d = counts.setdefault((r % pr, c % pc), {})
            d[v] = d.get(v, 0) + 1
    consensus = {k: max(d, key=d.get) for k, d in counts.items()}

    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == HOLE:
                key = (r % pr, c % pc)
                if key in consensus:
                    T[(r, c)] = consensus[key]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
