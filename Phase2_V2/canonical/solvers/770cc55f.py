def infer_T(input_grid):
    """Infer the latent fill mask.

    A horizontal line of 2s splits the grid into a top region and a bottom
    region. The top edge row and bottom edge row each carry a colored marker.
    The marker with FEWER colored cells selects the region OPPOSITE to it for
    filling. The columns that get filled are the intersection of the top and
    bottom marker columns. Filled cells take color 4.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    # Locate the dividing line: a full row of 2s.
    line = None
    for r in range(H):
        if all(input_grid[r][c] == 2 for c in range(W)):
            line = r
            break

    T = [[None] * W for _ in range(H)]
    if line is None:
        return T

    # Marker columns on the top edge (row 0) and bottom edge (row H-1).
    top_cols = set(c for c in range(W) if input_grid[0][c] != 0)
    bot_cols = set(c for c in range(W) if input_grid[H - 1][c] != 0)
    inter = top_cols & bot_cols
    if not inter:
        return T

    # Smaller marker (by count of cells) -> fill the opposite region.
    if len(top_cols) <= len(bot_cols):
        # top is smaller (or equal) -> fill bottom region
        rows = range(line + 1, H - 1)
    else:
        # bottom is smaller -> fill top region
        rows = range(1, line)

    for r in rows:
        for c in inter:
            T[r][c] = 4
    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
