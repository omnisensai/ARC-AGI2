"""Canonical solver for ARC puzzle e95e3d8e.

The grid is a doubly-periodic pattern (a small tile repeated in both
directions). Rectangular blocks of the pattern have been corrupted to 0.
The transformation restores every corrupted cell to the value dictated by
the underlying period, recovered by consensus over all non-zero cells that
share the same residue modulo the tile periods.
"""

HOLE = 0


def _best_period(grid, axis, length, ortho):
    """Find the smallest period p along `axis` consistent with all
    non-hole cells. axis 0 = vertical (period over rows), 1 = horizontal."""
    H = len(grid)
    W = len(grid[0])
    candidates = []
    for p in range(1, length):
        ok = True
        for r in range(H):
            if not ok:
                break
            for c in range(W):
                if grid[r][c] == HOLE:
                    continue
                if axis == 0:
                    rr, cc = r + p, c
                else:
                    rr, cc = r, c + p
                if 0 <= rr < H and 0 <= cc < W:
                    if grid[rr][cc] != HOLE and grid[rr][cc] != grid[r][c]:
                        ok = False
                        break
        if ok:
            candidates.append(p)
    # smallest valid period that actually divides usefully
    return candidates[0] if candidates else length


def infer_T(input_grid):
    """Compute the latent repair mask: for every hole cell, derive the
    pattern color from periodic consensus."""
    H = len(input_grid)
    W = len(input_grid[0])

    py = _best_period(input_grid, 0, H, W)  # vertical period
    px = _best_period(input_grid, 1, W, H)  # horizontal period

    # Build consensus for each residue class (r % py, c % px).
    consensus = {}
    counts = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == HOLE:
                continue
            key = (r % py, c % px)
            sub = counts.setdefault(key, {})
            sub[v] = sub.get(v, 0) + 1
    for key, sub in counts.items():
        consensus[key] = max(sub, key=sub.get)

    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == HOLE:
                key = (r % py, c % px)
                if key in consensus:
                    T[r][c] = consensus[key]
    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
