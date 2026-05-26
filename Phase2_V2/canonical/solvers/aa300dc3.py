"""Canonical solver for ARC puzzle aa300dc3.

Rule
----
The grid is a blob of interior cells (color 0) carved out of a background of
color 5. Find the longest unbroken diagonal segment (either direction) that lies
entirely on interior 0-cells. If several diagonals share the maximum length, pick
the one whose line passes closest to the centroid of the 0-region. Recolor every
cell on that diagonal to 8.
"""

FILL = 8
INTERIOR = 0


def _diagonal_runs(grid):
    """All maximal contiguous runs of INTERIOR cells along both diagonal dirs."""
    H, W = len(grid), len(grid[0])
    runs = []
    # main diagonals: step (+1, +1), constant r - c
    for k in range(-H + 1, W):
        run = []
        for r in range(H):
            c = r - k
            if 0 <= c < W and grid[r][c] == INTERIOR:
                run.append((r, c))
            else:
                if run:
                    runs.append(tuple(run))
                run = []
        if run:
            runs.append(tuple(run))
    # anti diagonals: step (+1, -1), constant r + c
    for s in range(0, H + W - 1):
        run = []
        for r in range(H):
            c = s - r
            if 0 <= c < W and grid[r][c] == INTERIOR:
                run.append((r, c))
            else:
                if run:
                    runs.append(tuple(run))
                run = []
        if run:
            runs.append(tuple(run))
    return runs


def infer_T(input_grid):
    """Return the latent mask {(r,c): FILL} marking the chosen diagonal."""
    H, W = len(input_grid), len(input_grid[0])
    zeros = [(r, c) for r in range(H) for c in range(W)
             if input_grid[r][c] == INTERIOR]
    T = {}
    if not zeros:
        return T
    cr = sum(r for r, c in zeros) / len(zeros)
    cc = sum(c for r, c in zeros) / len(zeros)

    runs = _diagonal_runs(input_grid)
    if not runs:
        return T
    longest = max(len(run) for run in runs)
    candidates = [run for run in runs if len(run) == longest]

    def perp_dist(run):
        r0, c0 = run[0]
        r1, c1 = run[1] if len(run) > 1 else run[0]
        if (r1 - r0) == (c1 - c0):          # main diagonal, r - c constant
            return abs((cr - cc) - (r0 - c0))
        return abs((cr + cc) - (r0 + c0))   # anti diagonal, r + c constant

    chosen = min(candidates, key=perp_dist)
    for (r, c) in chosen:
        T[(r, c)] = FILL
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
