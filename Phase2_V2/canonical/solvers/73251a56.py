"""Canonical solver for ARC puzzle 73251a56.

Rule: the grid is a deterministic, transpose-symmetric "fan" pattern. The main
diagonal is a constant color D. Off the diagonal (using transpose symmetry to
work in the upper triangle, d = c - r >= 0):
  - d == 0            -> D
  - 1 <= d <= r+1     -> S, the color just before D in the color cycle
  - beyond that       -> consecutive bands of width (r+2) cycling through
                         colors 1..maxColor, starting at D.
The colors used are 1..maxColor rotated so the cycle begins at D. Some cells are
occluded by color-0 "noise" blocks; those (and only those) are repaired by
regenerating the underlying pattern. infer_T derives D (majority of the
non-zero main-diagonal values) and maxColor (max non-zero color) from the input
alone, rebuilds the clean pattern, and marks each 0 cell with its true color.
"""

from collections import Counter


def _build_pattern(D, maxC, H, W):
    cycle = [((D - 1 + k) % maxC) + 1 for k in range(maxC)]
    S = cycle[-1]  # color just before D when wrapping
    g = [[0] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            # transpose symmetry: reduce to upper triangle r <= c
            rr, cc = (r, c) if r <= c else (c, r)
            d = cc - rr
            if d == 0:
                v = D
            else:
                e = d - 1
                if e < rr + 1:
                    v = S
                else:
                    f = e - (rr + 1)
                    b = f // (rr + 2)
                    v = cycle[b % maxC]
            g[r][c] = v
    return g


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # D = diagonal color (majority of non-zero values on the main diagonal)
    diag = [input_grid[i][i] for i in range(min(H, W)) if input_grid[i][i] != 0]
    D = Counter(diag).most_common(1)[0][0]
    # maxColor = largest non-zero color present
    maxC = max(v for row in input_grid for v in row if v != 0)
    pattern = _build_pattern(D, maxC, H, W)
    # latent mask: only the occluded (0) cells get repaired
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0:
                T[(r, c)] = pattern[r][c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
