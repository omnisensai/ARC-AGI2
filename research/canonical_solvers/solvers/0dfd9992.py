"""Canonical solver for ARC puzzle 0dfd9992.

Rule: the grid is a doubly-periodic tiling with some cells erased to the hole
color 0. Infer the smallest horizontal period pc and vertical period pr that are
consistent with every pair of non-hole cells (treating holes as wildcards), build
a consensus value for each residue class (r % pr, c % pc) from the surviving
non-hole cells, then fill each hole with its class's consensus value.
"""

HOLE = 0


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    def compatible(a, b):
        return a == HOLE or b == HOLE or a == b

    # smallest horizontal period: grid[r][c] agrees with grid[r][c+p]
    pc = W
    for p in range(1, W + 1):
        if all(
            compatible(input_grid[r][c], input_grid[r][c + p])
            for r in range(H)
            for c in range(W - p)
        ):
            pc = p
            break

    # smallest vertical period: grid[r][c] agrees with grid[r+p][c]
    pr = H
    for p in range(1, H + 1):
        if all(
            compatible(input_grid[r][c], input_grid[r + p][c])
            for c in range(W)
            for r in range(H - p)
        ):
            pr = p
            break

    # consensus tile value per residue class from surviving cells
    consensus = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != HOLE:
                consensus[(r % pr, c % pc)] = v

    # latent mask: only the hole cells get rewritten
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == HOLE:
                key = (r % pr, c % pc)
                if key in consensus:
                    T[r][c] = consensus[key]
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
