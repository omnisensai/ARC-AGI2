def infer_T(input_grid):
    """Infer a latent transformation mask.

    The input is composed of solid-colored rows.  We extract the set of
    distinct row colors (in order of first appearance) and build a
    checkerboard mask: each cell is repainted to one of the two band colors
    according to the parity of (row + col), anchored so that the top-left
    cell keeps its original (first-row) color.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    # Distinct colors by row (each row is solid in this family), preserving
    # first-appearance order.
    colors = []
    for r in range(H):
        c = input_grid[r][0]
        if c not in colors:
            colors.append(c)

    T = [[None] * W for _ in range(H)]
    if len(colors) < 2:
        return T  # nothing to interleave

    a, b = colors[0], colors[1]
    for r in range(H):
        for c in range(W):
            want = a if (r + c) % 2 == 0 else b
            if input_grid[r][c] != want:
                T[r][c] = want
    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
