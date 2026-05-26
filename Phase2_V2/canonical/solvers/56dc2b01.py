def infer_T(input_grid):
    """Latent mask for puzzle 56dc2b01.

    Structure: a full-row or full-column wall of color 2, and a color-3 shape
    sitting somewhere on one side of it. Rule: slide the shape (unchanged) until
    its near edge is adjacent to the wall, then draw a color-8 line one cell past
    the shape's far edge (opposite side from the wall), spanning the full grid.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}  # (r,c) -> new color

    wall_row = next((r for r in range(H)
                     if all(input_grid[r][c] == 2 for c in range(W))), None)
    wall_col = next((c for c in range(W)
                     if all(input_grid[r][c] == 2 for r in range(H))), None)

    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 3]
    if not cells:
        return T
    r0 = min(r for r, c in cells); r1 = max(r for r, c in cells)
    c0 = min(c for r, c in cells); c1 = max(c for r, c in cells)

    if wall_row is not None:
        height = r1 - r0
        if r0 > wall_row:          # shape below the wall -> slide up
            nr0 = wall_row + 1
            eight_row = nr0 + height + 1
        else:                       # shape above the wall -> slide down
            nr0 = wall_row - 1 - height
            eight_row = nr0 - 1
        dr = nr0 - r0
        for r, c in cells:
            T[(r, c)] = 0
        for r, c in cells:
            T[(r + dr, c)] = 3
        if 0 <= eight_row < H:
            for c in range(W):
                T[(eight_row, c)] = 8

    elif wall_col is not None:
        width = c1 - c0
        if c0 > wall_col:          # shape right of the wall -> slide left
            nc0 = wall_col + 1
            eight_col = nc0 + width + 1
        else:                       # shape left of the wall -> slide right
            nc0 = wall_col - 1 - width
            eight_col = nc0 - 1
        dc = nc0 - c0
        for r, c in cells:
            T[(r, c)] = 0
        for r, c in cells:
            T[(r, c + dc)] = 3
        if 0 <= eight_col < W:
            for r in range(H):
                T[(r, eight_col)] = 8

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
