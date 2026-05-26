def _cells(grid, v):
    return [(r, c) for r, row in enumerate(grid)
            for c, vv in enumerate(row) if vv == v]


def infer_T(input_grid):
    """Latent mask: translate the color-2 shape so its bounding-box center
    aligns with the center of the box defined by the four color-3 markers.
    Returns a dict {(r,c): new_color}. The four markers stay fixed; the
    background-2 shape is removed from its old position and redrawn centered.
    """
    H, W = len(input_grid), len(input_grid[0])

    markers = _cells(input_grid, 3)
    shape = _cells(input_grid, 2)
    if not markers or not shape:
        return {}

    mrs = sorted(set(r for r, c in markers))
    mcs = sorted(set(c for r, c in markers))
    # center of the marker box (use full span min..max)
    cr2 = mrs[0] + mrs[-1]            # 2 * center_row
    cc2 = mcs[0] + mcs[-1]            # 2 * center_col

    sr0 = min(r for r, c in shape)
    sr1 = max(r for r, c in shape)
    sc0 = min(c for r, c in shape)
    sc1 = max(c for r, c in shape)

    # new bbox center should match the marker-box center:
    # new_r0 + new_r1 == cr2, with same height -> shift rows
    # (sr0+sr1) + 2*dr == cr2
    dr2 = cr2 - (sr0 + sr1)
    dc2 = cc2 - (sc0 + sc1)
    assert dr2 % 2 == 0 and dc2 % 2 == 0, "non-integer centering"
    dr = dr2 // 2
    dc = dc2 // 2

    T = {}
    # clear the old shape cells (back to background 0)
    for (r, c) in shape:
        T[(r, c)] = 0
    # draw the shape at the centered location
    for (r, c) in shape:
        nr, nc = r + dr, c + dc
        if 0 <= nr < H and 0 <= nc < W:
            T[(nr, nc)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
