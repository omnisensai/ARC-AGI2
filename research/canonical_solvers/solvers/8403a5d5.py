def infer_T(input_grid):
    """Infer the latent overwrite mask {(r,c): color} from input structure.

    The input is a blank grid with a single colored marker in the bottom row.
    From the marker column c0 we grow vertical full-height lines at columns
    c0, c0+2, c0+4, ... (the marker color). The columns in between (c0+1,
    c0+3, ...) get a single 5: alternating between the top row and the bottom
    row, starting at the top for the first gap column.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    # Locate the single non-zero marker cell.
    marker = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0:
                marker = (r, c, input_grid[r][c])
                break
        if marker is not None:
            break
    if marker is None:
        return {}

    _, c0, color = marker
    T = {}

    # Vertical lines in the marker color every 2 columns from c0.
    for lc in range(c0, W, 2):
        for r in range(H):
            T[(r, lc)] = color

    # Gap columns (offset by 1) get a single 5, alternating top/bottom.
    for k, gc in enumerate(range(c0 + 1, W, 2)):
        row = 0 if k % 2 == 0 else H - 1
        T[(row, gc)] = 5

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
