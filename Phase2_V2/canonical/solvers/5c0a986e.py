def _bbox(cells):
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    return min(rs), max(rs), min(cs), max(cs)


def infer_T(input_grid):
    """Infer the diagonal-ray transformation mask.

    Two solid 2x2 squares (colors 1 and 2) sit on a background-0 grid.
    Each square emits a diagonal ray of its own color along the main
    ('\\') diagonal, continuing to the grid edge:
      - color 1: from its top-left corner, stepping up-left (-1,-1)
      - color 2: from its bottom-right corner, stepping down-right (+1,+1)
    The mask is {(r, c): color} for every ray cell.
    """
    H, W = len(input_grid), len(input_grid[0])
    comps = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0:
                comps.setdefault(v, []).append((r, c))

    # Per color: corner of the bounding box and diagonal step direction.
    # color 1 -> top-left corner, step (-1,-1); color 2 -> bottom-right, (+1,+1)
    spec = {
        1: ("topleft", (-1, -1)),
        2: ("botright", (1, 1)),
    }

    T = {}
    for color, cells in comps.items():
        if color not in spec:
            continue
        r0, r1, c0, c1 = _bbox(cells)
        corner_kind, (dr, dc) = spec[color]
        if corner_kind == "topleft":
            cr, cc = r0, c0
        else:  # botright
            cr, cc = r1, c1
        r, c = cr + dr, cc + dc
        while 0 <= r < H and 0 <= c < W:
            T[(r, c)] = color
            r += dr
            c += dc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
