"""Canonical solver for ARC puzzle ea959feb.

The grid is a doubly-periodic tiled pattern that has been corrupted by
rectangular blobs of noise. We recover the latent period along each axis by
consensus voting (the noise is a minority within each residue class), build a
consensus template, and repair every cell that disagrees with the template.
"""

from collections import Counter


def _col_period_score(grid, pc):
    """Agreement fraction when grid is folded with column period pc."""
    H, W = len(grid), len(grid[0])
    groups = {}
    for r in range(H):
        for c in range(W):
            groups.setdefault((r, c % pc), Counter())[grid[r][c]] += 1
    agree = tot = 0
    for cnt in groups.values():
        agree += max(cnt.values())
        tot += sum(cnt.values())
    return agree / tot


def _row_period_score(grid, pr):
    """Agreement fraction when grid is folded with row period pr."""
    H, W = len(grid), len(grid[0])
    groups = {}
    for r in range(H):
        for c in range(W):
            groups.setdefault((r % pr, c), Counter())[grid[r][c]] += 1
    agree = tot = 0
    for cnt in groups.values():
        agree += max(cnt.values())
        tot += sum(cnt.values())
    return agree / tot


def _best_period(score_func, length, thresh=0.85):
    """Smallest non-trivial period whose consensus agreement clears thresh.

    Excludes the full-dimension period (which is trivially perfect because
    each residue class has a single member). Falls back to the best-scoring
    period if none clears the threshold.
    """
    best = None
    for p in range(1, length):
        frac = score_func(p)
        if best is None or frac > best[0] + 1e-9:
            best = (frac, p)
        if frac >= thresh:
            return p
    return best[1]


def infer_T(input_grid):
    """Infer the repair mask {(r, c): new_color} from the periodic structure."""
    H, W = len(input_grid), len(input_grid[0])
    pc = _best_period(lambda p: _col_period_score(input_grid, p), W)
    pr = _best_period(lambda p: _row_period_score(input_grid, p), H)

    groups = {}
    for r in range(H):
        for c in range(W):
            groups.setdefault((r % pr, c % pc), Counter())[input_grid[r][c]] += 1
    template = {k: cnt.most_common(1)[0][0] for k, cnt in groups.items()}

    T = {}
    for r in range(H):
        for c in range(W):
            v = template[(r % pr, c % pc)]
            if input_grid[r][c] != v:
                T[(r, c)] = v
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
