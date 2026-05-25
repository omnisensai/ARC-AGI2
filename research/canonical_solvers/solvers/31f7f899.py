from collections import Counter


def _axis_and_bg(grid):
    """Find the background color and the orientation/index of the line of 6s.

    Returns (bg, orient, axis) where orient is 'row' or 'col' and axis is the
    index of the 6-line.
    """
    H, W = len(grid), len(grid[0])
    cnt = Counter(v for row in grid for v in row)
    bg = cnt.most_common(1)[0][0]
    # The axis is a full line (row or col) containing several 6s.
    for r in range(H):
        if sum(1 for c in range(W) if grid[r][c] == 6) >= 2:
            return bg, 'row', r
    for c in range(W):
        if sum(1 for r in range(H) if grid[r][c] == 6) >= 2:
            return bg, 'col', c
    return bg, None, None


def _bars(grid, bg, orient, axis):
    """Each bar is a coloured segment perpendicular to the 6-axis, centred on it.

    Returns a list of (pos, color, half) sorted by pos, where pos is the index
    along the axis (column for a row-axis), color is the bar colour and half is
    the number of cells the bar extends on each side of the axis.
    """
    H, W = len(grid), len(grid[0])
    bars = []
    if orient == 'row':
        for c in range(W):
            cells = [grid[r][c] for r in range(H) if grid[r][c] not in (bg, 6)]
            if not cells:
                continue
            color = cells[0]
            rs = [r for r in range(H) if grid[r][c] == color]
            half = max(abs(r - axis) for r in rs)
            bars.append((c, color, half))
    else:
        for r in range(H):
            cells = [grid[r][c] for c in range(W) if grid[r][c] not in (bg, 6)]
            if not cells:
                continue
            color = cells[0]
            cs = [c for c in range(W) if grid[r][c] == color]
            half = max(abs(c - axis) for c in cs)
            bars.append((r, color, half))
    bars.sort()
    return bars


def infer_T(input_grid):
    """Build the latent overwrite mask.

    The bars perpendicular to the 6-axis keep their position and colour but have
    their half-lengths reassigned: the multiset of half-lengths is sorted
    ascending and handed out to the bars in order of position along the axis.
    Every bar stays centred on the axis line.
    """
    H, W = len(input_grid), len(input_grid[0])
    bg, orient, axis = _axis_and_bg(input_grid)
    T = {}
    if orient is None:
        return T, bg
    bars = _bars(input_grid, bg, orient, axis)
    if not bars:
        return T, bg
    halves = sorted(b[2] for b in bars)

    # First, clear every existing bar cell (set to bg) so old lengths vanish.
    for pos, color, half in bars:
        if orient == 'row':
            for r in range(H):
                if input_grid[r][pos] == color:
                    T[(r, pos)] = bg
        else:
            for c in range(W):
                if input_grid[pos][c] == color:
                    T[(pos, c)] = bg

    # Then paint each bar with its newly assigned half-length, centred on axis.
    for (pos, color, _old), new_half in zip(bars, halves):
        if orient == 'row':
            for d in range(-new_half, new_half + 1):
                r = axis + d
                if 0 <= r < H:
                    T[(r, pos)] = color
        else:
            for d in range(-new_half, new_half + 1):
                c = axis + d
                if 0 <= c < W:
                    T[(pos, c)] = color
    return T, bg


def apply_T(input_grid, T_bg):
    T, _bg = T_bg
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
