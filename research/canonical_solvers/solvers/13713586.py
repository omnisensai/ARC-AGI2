from collections import defaultdict


def _find_wall(grid):
    """Locate the full row or column of color 5 (the wall)."""
    H, W = len(grid), len(grid[0])
    for r in range(H):
        if all(grid[r][c] == 5 for c in range(W)):
            return ('row', r)
    for c in range(W):
        if all(grid[r][c] == 5 for r in range(H)):
            return ('col', c)
    return None


def infer_T(input_grid):
    """Each colored bar is extruded as a rectangle from its own line up to
    (but not onto) the wall. Bars perpendicular-extrude toward the wall.
    Where extrusions overlap, the bar whose line is NEAREST the wall wins,
    so we paint far-to-near and let nearer bars overwrite farther ones."""
    H, W = len(input_grid), len(input_grid[0])
    wall = _find_wall(input_grid)
    T = {}
    if wall is None:
        return T
    side, idx = wall

    # group every non-background, non-wall cell by its color into one bar
    cells = defaultdict(list)
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v not in (0, 5):
                cells[v].append((r, c))

    bars = []
    for color, cs in cells.items():
        rs = [p[0] for p in cs]
        cc = [p[1] for p in cs]
        bars.append((color, min(rs), max(rs), min(cc), max(cc)))

    def near_dist(bar):
        color, r0, r1, c0, c1 = bar
        if side == 'row':
            return min(abs(r0 - idx), abs(r1 - idx))
        return min(abs(c0 - idx), abs(c1 - idx))

    # farthest from wall first; nearer bars painted later overwrite them
    bars.sort(key=near_dist, reverse=True)

    for color, r0, r1, c0, c1 in bars:
        if side == 'row':
            rr = range(idx + 1, r1 + 1) if idx < r0 else range(r0, idx)
            for r in rr:
                for c in range(c0, c1 + 1):
                    T[(r, c)] = color
        else:
            cc_range = range(idx + 1, c1 + 1) if idx < c0 else range(c0, idx)
            for r in range(r0, r1 + 1):
                for c in cc_range:
                    T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
