def infer_T(input_grid):
    """Latent mask: mirror the top colored block to the bottom edge.

    The input has a contiguous block of non-background rows at the top and
    background-filled rows below. The transformation places a vertically
    mirrored copy of that top block flush against the bottom of the grid.
    """
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color (fills the empty lower region)
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # contiguous top block of fully non-background rows
    block_rows = []
    for r in range(H):
        if all(input_grid[r][c] != bg for c in range(W)):
            block_rows.append(r)
        else:
            break
    # mirrored copy placed flush at the bottom (reversed row order)
    T = {}
    for i, r in enumerate(block_rows):
        dest = H - 1 - i
        for c in range(W):
            T[(dest, c)] = input_grid[r][c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
