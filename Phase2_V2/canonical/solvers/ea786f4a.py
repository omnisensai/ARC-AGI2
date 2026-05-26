def infer_T(input_grid):
    """Infer the latent transformation mask.

    The input has a uniform background with a single marker cell (color 0).
    The transformation draws two diagonals (an X) through the marker: every
    cell whose row/col offset from the marker has equal absolute value becomes
    the marker color. Returns a mask {(r, c): new_color}.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Find background as the most frequent color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Find the single marker cell (the non-background cell).
    marker = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg:
                marker = (r, c)
                break
        if marker is not None:
            break
    if marker is None:
        return {}

    r0, c0 = marker
    mcolor = input_grid[r0][c0]

    mask = {}
    for r in range(H):
        for c in range(W):
            if abs(r - r0) == abs(c - c0):
                mask[(r, c)] = mcolor
    return mask


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
