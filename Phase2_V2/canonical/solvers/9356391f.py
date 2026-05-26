def infer_T(input_grid):
    """Infer the latent overwrite mask {(r,c): color}.

    Row 0 holds a colour palette; row 1 is a full separator line; a lone seed
    pixel sits below it. The palette maps directly onto concentric Chebyshev
    rings centred on the seed (palette index i -> ring radius i), with 0 meaning
    an empty (background) ring. If a ring is clipped by the grid boundary, that
    ring's palette cell in row 0 is overwritten with the separator colour.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}

    # separator colour: the color filling a full uniform non-zero row
    sep = None
    for r in range(H):
        row = input_grid[r]
        if row[0] != 0 and all(v == row[0] for v in row):
            sep = row[0]
            break

    # palette: row 0 from column 0 up to the last non-zero entry (gaps kept)
    row0 = input_grid[0]
    nz = [c for c in range(W) if row0[c] != 0]
    if not nz:
        return T
    palette = row0[:max(nz) + 1]

    # seed: the lone non-zero pixel below the separator line
    seed = None
    for r in range(2, H):
        for c in range(W):
            if input_grid[r][c] != 0:
                seed = (r, c)
                break
        if seed:
            break
    if seed is None:
        return T
    sr, sc = seed

    # concentric Chebyshev rings
    for rad, color in enumerate(palette):
        clipped = (sr - rad < 0) or (sr + rad >= H) or (sc - rad < 0) or (sc + rad >= W)
        if color != 0:
            for r in range(sr - rad, sr + rad + 1):
                for c in range(sc - rad, sc + rad + 1):
                    if 0 <= r < H and 0 <= c < W and max(abs(r - sr), abs(c - sc)) == rad:
                        T[(r, c)] = color
        # clipped ring -> blank its palette cell (row 0, column == radius index)
        if clipped and sep is not None and rad < W and row0[rad] != 0:
            T[(0, rad)] = sep

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
