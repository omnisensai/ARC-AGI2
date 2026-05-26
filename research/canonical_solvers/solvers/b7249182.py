def infer_T(input_grid):
    """Two colored markers lie on a common row (horizontal pair) or common
    column (vertical pair).  A square-outline 'box' is drawn centered on the
    line between them: 5 cells deep (perpendicular to the axis, centered on the
    marker line) and 4 cells along the axis (centered between the two markers,
    split 2/2 so each half takes its nearest marker's color).  An arm of each
    marker's color runs along the axis from the marker (inclusive) up to the
    near edge of the box.  Returns a dict {(r,c): color} mask."""
    H, W = len(input_grid), len(input_grid[0])
    markers = [(r, c, input_grid[r][c])
               for r in range(H) for c in range(W) if input_grid[r][c] != 0]
    T = {}
    if len(markers) != 2:
        return T
    (r1, c1, v1), (r2, c2, v2) = markers

    if r1 == r2:
        # horizontal pair: axis = columns, perpendicular = rows
        axis = 'h'
        row = r1
        a1, a2 = c1, c2          # along-axis coords of the two markers
    elif c1 == c2:
        axis = 'v'
        col = c1
        a1, a2 = r1, r2
    else:
        return T

    # order so m1 is the lower along-axis coord
    if a1 > a2:
        a1, a2 = a2, a1
        v1, v2 = v2, v1

    center = (a1 + a2) / 2.0          # always an X.5 value
    # the 4 box cells along the axis
    box_coords = [int(center - 1.5), int(center - 0.5),
                  int(center + 0.5), int(center + 1.5)]
    left_box = box_coords[:2]         # nearest marker1 -> v1
    right_box = box_coords[2:]        # nearest marker2 -> v2
    near_left = box_coords[0]         # near edge for marker1's arm
    near_right = box_coords[-1]       # near edge for marker2's arm

    def setc(r, c, v):
        if 0 <= r < H and 0 <= c < W:
            T[(r, c)] = v

    if axis == 'h':
        depths = [row - 2, row - 1, row, row + 1, row + 2]
        top, bot = depths[0], depths[-1]
        # box outline: top & bottom edges across all 4 box columns
        for cc in left_box:
            setc(top, cc, v1); setc(bot, cc, v1)
        for cc in right_box:
            setc(top, cc, v2); setc(bot, cc, v2)
        # left & right vertical edges of the box
        for rr in depths:
            setc(rr, box_coords[0], v1)
            setc(rr, box_coords[-1], v2)
        # arms along the row from each marker to the box near edge
        for cc in range(a1, near_left + 1):
            setc(row, cc, v1)
        for cc in range(near_right, a2 + 1):
            setc(row, cc, v2)
    else:
        depths = [col - 2, col - 1, col, col + 1, col + 2]
        left_d, right_d = depths[0], depths[-1]
        for rr in left_box:
            setc(rr, left_d, v1); setc(rr, right_d, v1)
        for rr in right_box:
            setc(rr, left_d, v2); setc(rr, right_d, v2)
        for cc in depths:
            setc(box_coords[0], cc, v1)
            setc(box_coords[-1], cc, v2)
        for rr in range(a1, near_left + 1):
            setc(rr, col, v1)
        for rr in range(near_right, a2 + 1):
            setc(rr, col, v2)
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
