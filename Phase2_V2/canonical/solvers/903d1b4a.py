def infer_T(input_grid):
    """Latent transformation mask.

    The grid is D4-symmetric (invariant under both mirrors, 180 rotation,
    both diagonals, and the two quarter rotations). Color 3 is corruption
    noise overlaid on top of the true symmetric grid. For each noise cell we
    recover the true color from a non-noise cell in its D4 orbit. Returns a
    dict {(r,c): recovered_color} covering only the corrupted cells.
    """
    H, W = len(input_grid), len(input_grid[0])
    NOISE = 3

    def orbit(r, c):
        # full dihedral group D4 on a square grid (H == W)
        return [
            (r, W - 1 - c),          # horizontal mirror
            (H - 1 - r, c),          # vertical mirror
            (H - 1 - r, W - 1 - c),  # rot 180
            (c, r),                  # main-diagonal transpose
            (W - 1 - c, H - 1 - r),  # anti-diagonal transpose
            (c, H - 1 - r),          # rot 90
            (W - 1 - c, r),          # rot 270
        ]

    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != NOISE:
                continue
            for rr, cc in orbit(r, c):
                if 0 <= rr < H and 0 <= cc < W and input_grid[rr][cc] != NOISE:
                    T[(r, c)] = input_grid[rr][cc]
                    break
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
