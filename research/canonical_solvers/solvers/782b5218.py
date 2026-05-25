def infer_T(input_grid):
    """Infer the recolor mask.

    Structure: a marker color (2) forms a diagonal/horizontal staircase band that
    splits the grid. For each column, the 2-cells are preserved; every other cell
    is recolored based on its position relative to that column's band:
      - cells above the topmost 2 in the column -> background 0
      - cells from the band downward (below the topmost 2) -> the foreground color
    Columns with no 2 are entirely background (0).
    The mask T is {(r,c): new_color} for every cell that must be overwritten.
    """
    H, W = len(input_grid), len(input_grid[0])
    MARKER = 2

    # Foreground = the single non-zero, non-marker color present in the grid.
    palette = set(v for row in input_grid for v in row) - {0, MARKER}
    fg = next(iter(palette)) if palette else 0

    T = {}
    for c in range(W):
        twos = [r for r in range(H) if input_grid[r][c] == MARKER]
        if not twos:
            for r in range(H):
                T[(r, c)] = 0
            continue
        top = min(twos)
        for r in range(H):
            if input_grid[r][c] == MARKER:
                continue  # marker preserved (not in mask)
            T[(r, c)] = 0 if r < top else fg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
