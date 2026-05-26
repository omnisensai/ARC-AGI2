"""Canonical solver for ARC puzzle 484b58aa.

Rule: the input is a doubly-periodic tiling that has been partially occluded
by rectangular patches of 0. Recover the underlying period (smallest
horizontal period ph, smallest vertical period pv consistent with all
non-zero cells), then repaint every occluded (0) cell with the consensus
color of all cells sharing its (row % pv, col % ph) phase.

Canonical latent-T form: infer_T builds a dict mask {(r,c): color} of the
cells to overwrite (the 0 holes), apply_T copies the input and writes them.
"""

from collections import Counter


def smallest_period_h(grid):
    """Smallest column period p such that all aligned non-zero cells agree."""
    H, W = len(grid), len(grid[0])
    for p in range(1, W):
        good = True
        for r in range(H):
            for c in range(W - p):
                a, b = grid[r][c], grid[r][c + p]
                if a != 0 and b != 0 and a != b:
                    good = False
                    break
            if not good:
                break
        if good:
            return p
    return W


def smallest_period_v(grid):
    """Smallest row period p such that all aligned non-zero cells agree."""
    H, W = len(grid), len(grid[0])
    for p in range(1, H):
        good = True
        for r in range(H - p):
            for c in range(W):
                a, b = grid[r][c], grid[r + p][c]
                if a != 0 and b != 0 and a != b:
                    good = False
                    break
            if not good:
                break
        if good:
            return p
    return H


def infer_T(input_grid):
    """Latent transformation mask: {(r,c): new_color} for occluded cells."""
    H, W = len(input_grid), len(input_grid[0])
    ph = smallest_period_h(input_grid)
    pv = smallest_period_v(input_grid)

    # Consensus color for every (row-phase, col-phase) class.
    cons = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == 0:
                continue
            key = (r % pv, c % ph)
            cons.setdefault(key, Counter())[v] += 1

    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0:
                key = (r % pv, c % ph)
                if key in cons:
                    T[(r, c)] = cons[key].most_common(1)[0][0]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
