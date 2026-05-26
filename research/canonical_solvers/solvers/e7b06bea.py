def infer_T(input_grid):
    """Infer a latent transformation mask {(r,c): new_color}.

    Structure of the input:
      - A vertical run of '5' markers occupies the top of column 0; the number
        of 5s (nfive) sets the vertical block height.
      - On the right side there are k adjacent constant vertical stripe columns,
        each a single nonzero (non-5) color.
    Transformation:
      - All stripe cells are cleared to 0.
      - A new single column, placed one cell to the left of the leftmost stripe
        column, is filled top-to-bottom by cycling through the stripe colors in
        blocks of height nfive.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    # Count the vertical run of 5s in column 0.
    nfive = 0
    for r in range(H):
        if input_grid[r][0] == 5:
            nfive += 1
    if nfive == 0:
        nfive = 1

    # Identify stripe columns: constant nonzero (non-5) value down the column.
    stripe_cols = []
    for c in range(W):
        vals = set(input_grid[r][c] for r in range(H))
        if len(vals) == 1:
            v = next(iter(vals))
            if v != 0 and v != 5:
                stripe_cols.append(c)
    stripe_cols.sort()

    T = {}
    if not stripe_cols:
        return T

    colors = [input_grid[0][c] for c in stripe_cols]

    # Clear all stripe cells.
    for c in stripe_cols:
        for r in range(H):
            T[(r, c)] = 0

    # Build the new column: one cell left of the leftmost stripe.
    out_col = stripe_cols[0] - 1
    if out_col < 0:
        return T
    for r in range(H):
        block = r // nfive
        color = colors[block % len(colors)]
        # Do not overwrite the 5 markers (preserve existing non-background).
        if input_grid[r][out_col] == 0:
            T[(r, out_col)] = color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
