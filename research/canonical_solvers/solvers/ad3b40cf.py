"""Canonical solver for ARC puzzle ad3b40cf.

Rule: a line of color 1 acts as a mirror axis (vertical / horizontal /
main-diagonal / anti-diagonal, detected from the 1-cells). Two non-background
colored shape groups exist; the color whose cells are FEWER in total is
reflected across the mirror onto the empty side, while the more populous color
stays put. infer_T builds the mask of reflected cells; apply_T overlays them.
"""

from collections import Counter

BG = 8
LINE = 1


def _mirror_fn(g):
    """Detect the line of LINE-colored cells and return a reflection function."""
    H, W = len(g), len(g[0])
    line = [(r, c) for r in range(H) for c in range(W) if g[r][c] == LINE]
    if not line:
        return None
    rows = set(r for r, c in line)
    cols = set(c for r, c in line)
    sums = set(r + c for r, c in line)
    diffs = set(r - c for r, c in line)
    if len(rows) == 1:                 # horizontal mirror at row rr
        rr = next(iter(rows))
        return lambda r, c: (2 * rr - r, c)
    if len(cols) == 1:                 # vertical mirror at col cc
        cc = next(iter(cols))
        return lambda r, c: (r, 2 * cc - c)
    if len(sums) == 1:                 # anti-diagonal r+c == k
        k = next(iter(sums))
        return lambda r, c: (k - c, k - r)
    if len(diffs) == 1:                # main diagonal r-c == k
        k = next(iter(diffs))
        return lambda r, c: (c + k, r - k)
    return None


def infer_T(input_grid):
    """Compute the latent transformation mask {(r,c): color}."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    refl = _mirror_fn(input_grid)
    if refl is None:
        return T
    counts = Counter(
        v for row in input_grid for v in row if v not in (BG, LINE)
    )
    if not counts:
        return T
    # The color with the fewest total cells is the one that mirrors.
    target = min(counts, key=lambda col: (counts[col], col))
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == target:
                nr, nc = refl(r, c)
                if 0 <= nr < H and 0 <= nc < W:
                    T[(nr, nc)] = target
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
