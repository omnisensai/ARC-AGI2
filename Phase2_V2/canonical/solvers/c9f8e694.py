def infer_T(input_grid):
    """Infer a latent recolor mask.

    Structure: column 0 of each row acts as a legend/key giving the color
    that any filler cells (value 5) in that row should take. We build a mask
    {(r, c): legend_color} for every cell holding the filler value 5.
    """
    H, W = len(input_grid), len(input_grid[0])
    FILLER = 5
    T = {}
    for r in range(H):
        legend = input_grid[r][0]
        for c in range(W):
            if input_grid[r][c] == FILLER:
                T[(r, c)] = legend
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
