"""Canonical solver for ARC puzzle 5b526a93.

Rule: The input contains 3x3 hollow squares (color-1 border, hollow center)
arranged on a lattice. They occupy a set R of distinct top-left rows and a set
C of distinct top-left columns. The full Cartesian product R x C defines every
lattice slot. Slots already holding a 1-square stay as-is; every other slot is
filled with an 8-square (8-border, hollow center). infer_T builds the mask of
the new 8-cells; apply_T overwrites only those cells.
"""

SQUARE = [1, 1, 1, 1, 0, 1, 1, 1, 1]


def _find_squares(g):
    H, W = len(g), len(g[0])
    sqs = []
    for r in range(H - 2):
        for c in range(W - 2):
            block = [g[r + dr][c + dc] for dr in range(3) for dc in range(3)]
            if block == SQUARE:
                sqs.append((r, c))
    return sqs


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    sqs = _find_squares(input_grid)
    sq_set = set(sqs)
    rows = sorted(set(r for r, c in sqs))
    cols = sorted(set(c for r, c in sqs))
    T = [[None] * W for _ in range(H)]
    for r in rows:
        for c in cols:
            if (r, c) in sq_set:
                continue  # existing 1-square: leave untouched
            for dr in range(3):
                for dc in range(3):
                    if (dr, dc) != (1, 1):  # hollow center stays 0
                        T[r + dr][c + dc] = 8
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
