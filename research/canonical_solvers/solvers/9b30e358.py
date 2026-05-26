from collections import Counter


def infer_T(input_grid):
    """Find the pattern block at the bottom of the grid and tile it upward.

    The non-background rows form a contiguous block anchored at the bottom of
    the grid. The latent transformation fills every row ABOVE that block by
    repeating the block periodically (period = block height), so the block
    itself stays fixed and the empty space above it is filled with copies.
    """
    H = len(input_grid)
    W = len(input_grid[0])
    counts = Counter(v for row in input_grid for v in row)
    bg = counts.most_common(1)[0][0]

    nonbg_rows = [r for r in range(H)
                  if any(input_grid[r][c] != bg for c in range(W))]
    T = [[None] * W for _ in range(H)]
    if not nonbg_rows:
        return T

    top = min(nonbg_rows)
    bottom = max(nonbg_rows)
    ph = bottom - top + 1  # pattern block height, anchored at the bottom

    # Fill rows above the original block by tiling the block periodically.
    for r in range(top):
        src = top + ((r - top) % ph)
        for c in range(W):
            T[r][c] = input_grid[src][c]
    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
