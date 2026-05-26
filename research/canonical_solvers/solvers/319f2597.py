def infer_T(input_grid):
    """Infer the latent transformation mask.

    The input contains a rectangular block of 0s. The transformation extends a
    cross/plus through that block: every cell sharing a row with the block and
    every cell sharing a column with the block is repainted to 0, EXCEPT cells
    that are already color 2, which are preserved (set to 2 in the mask).

    Returns T as a dict {(r, c): new_color}.
    """
    H, W = len(input_grid), len(input_grid[0])
    zeros = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 0]
    if not zeros:
        return {}
    block_rows = sorted(set(r for r, c in zeros))
    block_cols = sorted(set(c for r, c in zeros))

    strip = set()
    for r in block_rows:
        for c in range(W):
            strip.add((r, c))
    for c in block_cols:
        for r in range(H):
            strip.add((r, c))

    T = {}
    for (r, c) in strip:
        T[(r, c)] = 2 if input_grid[r][c] == 2 else 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
