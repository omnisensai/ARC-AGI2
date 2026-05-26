"""Canonical solver for ARC puzzle 1e97544e.

The grid is a deterministic "staircase" pattern:
  clean(r, c) = base[c % p]        if r <= c   (on/above the main diagonal)
              = base[(c + 1) % p]  if r >  c   (below the main diagonal)
where `base` is a linear period-p color sequence. Some cells are corrupted to
0; the task is to repair them back to the clean staircase value.

infer_T reconstructs `base`/period by consensus voting over the uncorrupted
cells (each cell at (r,c) votes for base[c] when r<=c, else base[c+1]), then
builds a mask of exactly the cells whose clean value differs from the input.
apply_T overwrites only those masked cells.
"""
from collections import Counter


def _infer_base(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    votes = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == 0:
                continue
            idx = c if r <= c else c + 1
            votes.setdefault(idx, Counter())[v] += 1
    base = {i: cnt.most_common(1)[0][0] for i, cnt in votes.items()}
    maxi = max(base)
    for p in range(1, maxi + 2):
        consistent = all((i + p) not in base or base[i] == base[i + p] for i in base)
        if not consistent:
            continue
        residues = {i % p for i in base}
        if residues != set(range(p)):
            continue
        arr = [None] * p
        for i, v in base.items():
            arr[i % p] = v
        if None not in arr:
            return p, arr
    return None, None


def infer_T(input_grid):
    """Latent mask: {(r, c): clean_color} for every cell whose clean staircase
    value differs from the (possibly corrupted) input."""
    H, W = len(input_grid), len(input_grid[0])
    p, base = _infer_base(input_grid)
    T = {}
    if base is None:
        return T

    def clean(r, c):
        return base[c % p] if r <= c else base[(c + 1) % p]

    for r in range(H):
        for c in range(W):
            cv = clean(r, c)
            if input_grid[r][c] != cv:
                T[(r, c)] = cv
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
