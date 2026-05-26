def infer_T(input_grid):
    """Infer the latent mask: a diagonal/straight 'bent line' of color 3 that
    connects the 2-marker to the 1-marker.

    Walking from the 2-marker toward the 1-marker the path is always:
      1 diagonal step, then a straight run along the dominant axis for
      ||dr|-|dc|| steps, then the remaining diagonal steps onto the 1-marker.
    Only the intermediate cells (not the markers themselves) are masked.
    """
    H, W = len(input_grid), len(input_grid[0])
    one = two = None
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == 1:
                one = (r, c)
            elif v == 2:
                two = (r, c)

    T = {}
    if one is None or two is None:
        return T

    sr, sc = two
    er, ec = one
    sgr = (er > sr) - (er < sr)   # sign of row direction toward the 1-marker
    sgc = (ec > sc) - (ec < sc)   # sign of col direction toward the 1-marker
    dr = abs(er - sr)
    dc = abs(ec - sc)
    ndiag = min(dr, dc)           # total diagonal steps
    nstr = abs(dr - dc)           # straight steps along the dominant axis
    vert = dr > dc                # dominant axis is vertical when more rows to cover

    # Step sequence from the 2-marker: one diagonal, the straight run, then the
    # rest of the diagonals.
    steps = ['D'] + ['S'] * nstr + ['D'] * (ndiag - 1)

    cur = (sr, sc)
    for s in steps:
        r, c = cur
        if s == 'D':
            cur = (r + sgr, c + sgc)
        elif vert:
            cur = (r + sgr, c)
        else:
            cur = (r, c + sgc)
        if cur != one and cur != two and 0 <= cur[0] < H and 0 <= cur[1] < W:
            T[cur] = 3

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
