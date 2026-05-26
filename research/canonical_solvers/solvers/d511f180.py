def infer_T(input_grid):
    """Infer a latent transformation mask.

    Structure: the grid contains two distinguished colors that are mutually
    swapped.  We detect this swap pair as the two colors A,B such that mapping
    A<->B (and leaving everything else fixed) is a consistent involution over
    the cells.  Concretely, ARC tasks of this family swap the two non-unique
    colors that interleave; here we detect them as the pair whose counts allow
    a clean swap.  We pick the swap pair as the two most frequent colors that
    are distinct, which form the mobile/background interplay of this puzzle.
    """
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1

    # The two colors involved in the swap are the two most frequent colors.
    ordered = sorted(counts, key=lambda c: (-counts[c], c))
    if len(ordered) < 2:
        return {}
    a, b = ordered[0], ordered[1]

    T = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == a:
                T[(r, c)] = b
            elif v == b:
                T[(r, c)] = a
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
