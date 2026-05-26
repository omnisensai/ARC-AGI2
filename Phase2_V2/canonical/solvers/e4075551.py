def infer_T(input_grid):
    """Infer a latent transformation mask {(r,c): color} from the marker layout.

    The input has a 0 background plus a handful of single-cell colored markers.
    Exactly five markers participate: the topmost/bottommost/leftmost/rightmost
    markers define the four edges of a rectangle (each donating its color and one
    boundary coordinate), and the remaining (central) marker sits inside the box.
    The transformation draws:
      - left/right colored columns spanning [top_row, bottom_row],
      - top/bottom colored rows spanning [left_col, right_col] (corners = row color),
      - a connector cross (color 5) along the center marker's row and column,
        restricted to the box interior, leaving the center marker untouched.
    """
    H, W = len(input_grid), len(input_grid[0])

    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # collect single-cell markers
    markers = []
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg:
                markers.append((r, c, v))

    T = {}
    if len(markers) < 5:
        return T

    # edge markers by extreme coordinate
    top = min(markers, key=lambda m: m[0])
    bottom = max(markers, key=lambda m: m[0])
    left = min(markers, key=lambda m: m[1])
    right = max(markers, key=lambda m: m[1])

    edge_set = {id(top), id(bottom), id(left), id(right)}
    center = None
    for m in markers:
        if id(m) not in edge_set:
            center = m
            break
    if center is None:
        return T

    top_r = top[0]
    bot_r = bottom[0]
    left_c = left[1]
    right_c = right[1]
    cr, cc = center[0], center[1]

    if not (top_r < bot_r and left_c < right_c):
        return T
    if not (top_r <= cr <= bot_r and left_c <= cc <= right_c):
        return T

    cross = 5

    # left / right columns over the full vertical extent
    for r in range(top_r, bot_r + 1):
        T[(r, left_c)] = left[2]
        T[(r, right_c)] = right[2]

    # connector cross interior: center column and center row (interior only)
    for r in range(top_r + 1, bot_r):
        if (cr, cc) != (r, cc):
            T[(r, cc)] = cross
    for c in range(left_c + 1, right_c):
        if (cr, cc) != (cr, c):
            T[(cr, c)] = cross

    # center marker stays its own color
    T[(cr, cc)] = center[2]

    # top / bottom rows span the full horizontal extent (corners take row color)
    for c in range(left_c, right_c + 1):
        T[(top_r, c)] = top[2]
        T[(bot_r, c)] = bottom[2]

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
