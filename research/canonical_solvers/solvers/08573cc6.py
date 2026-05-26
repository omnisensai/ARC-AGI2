def infer_T(input_grid):
    """Infer a latent change-mask {(r,c): color} describing a square spiral.

    The input holds two 'palette' colors in the top-left corner cells (0,0)
    and (0,1), and a single marker cell of color 1 somewhere in the grid.
    The output draws an expanding clockwise square spiral starting at the
    marker (first step LEFT, then DOWN, RIGHT, UP, repeating). Each straight
    segment is one cell longer than the previous (starting length 2), and the
    drawing color alternates per segment between palette color A (cells (0,0))
    and palette color B (cell (0,1)). The spiral grows until a step would
    leave the grid, drawing the boundary cell and then stopping.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Palette colors live in the two top-left corner cells.
    color_a = input_grid[0][0]
    color_b = input_grid[0][1]

    # Locate the marker (color 1).
    marker = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 1:
                marker = (r, c)
                break
        if marker is not None:
            break
    if marker is None:
        return {}

    T = {}
    if color_a == 0 and color_b == 0:
        return T

    # Square spiral: LEFT, DOWN, RIGHT, UP repeating.
    dirs = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    r, c = marker
    seg_len = 2          # first segment draws 2 cells
    seg_index = 0        # even -> color_a, odd -> color_b
    stop = False
    # A generous cap on number of segments (grid can never need more).
    for _ in range(4 * (H + W) + 8):
        dr, dc = dirs[seg_index % 4]
        color = color_a if seg_index % 2 == 0 else color_b
        for _ in range(seg_len):
            r += dr
            c += dc
            if not (0 <= r < H and 0 <= c < W):
                stop = True
                break
            T[(r, c)] = color
        if stop:
            break
        seg_index += 1
        seg_len += 1
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the cells named in the spiral mask.

    The marker cell (color 1) is preserved because the spiral path never
    revisits the marker's own coordinate.
    """
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    # Clear the two palette source cells (they are not part of the output).
    if H > 0 and W > 1:
        out[0][0] = 0
        out[0][1] = 0
    for (r, c), color in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
