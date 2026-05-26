def infer_T(input_grid):
    """Infer the latent fractal-stamp mask.

    The input contains a single small object that fits in a 3x3 bounding box.
    The output is a fractal: the 9x9 grid is split into a 3x3 arrangement of
    3x3 blocks; a block at position (br,bc) receives a stamped copy of the
    object iff the object cell at relative position (br,bc) is non-zero.

    T is a dict {(r,c): color} of cells to set in the output.
    """
    H, W = len(input_grid), len(input_grid[0])
    cells = [(r, c, input_grid[r][c])
             for r in range(H) for c in range(W) if input_grid[r][c] != 0]
    T = {}
    if not cells:
        return T
    color = cells[0][2]
    r0 = min(r for r, c, v in cells)
    c0 = min(c for r, c, v in cells)
    # Relative 3x3 pattern of the object.
    pat = [[0] * 3 for _ in range(3)]
    for r, c, v in cells:
        i, j = r - r0, c - c0
        if 0 <= i < 3 and 0 <= j < 3:
            pat[i][j] = v
    # Stamp the pattern into each block whose anchor cell is set.
    for br in range(3):
        for bc in range(3):
            if pat[br][bc] == 0:
                continue
            for i in range(3):
                for j in range(3):
                    if pat[i][j] != 0:
                        rr, cc = br * 3 + i, bc * 3 + j
                        if 0 <= rr < H and 0 <= cc < W:
                            T[(rr, cc)] = pat[i][j]
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    # Output is the fractal stamp on a blank canvas (background zeros).
    out = [[0] * W for _ in range(H)]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
