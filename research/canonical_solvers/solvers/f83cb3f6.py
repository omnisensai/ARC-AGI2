"""Canonical solver for ARC puzzle f83cb3f6.

Rule: the grid contains a contiguous "wall" line made of color 8 (a full row
segment or full column segment, possibly with internal gaps). Scattered single
dots of one other color are "attracted" toward the wall. For every wall cell
that actually holds an 8, on each side of the wall independently, if at least
one dot exists on that side along the same line position, a single dot is
placed in the cell immediately adjacent to the wall on that side. All original
dots are removed (overwritten with background). Positions where the wall has a
gap (no 8) catch nothing.

Canonical latent-T form: infer_T builds a {(r,c): color} mask describing every
cell that changes; apply_T copies the input and overwrites only those cells.
"""


def _find_wall(grid):
    """Return ('col', index) or ('row', index) for the 8-wall line.

    The wall is the single row or column that contains the most 8 cells. The
    line may contain internal gaps; those gaps are handled by the projection
    loop, which only acts on cells that actually hold an 8.
    """
    H, W = len(grid), len(grid[0])
    best = None  # (count, orient, idx)

    for c in range(W):
        cnt = sum(1 for r in range(H) if grid[r][c] == 8)
        if cnt and (best is None or cnt > best[0]):
            best = (cnt, 'col', c)

    for r in range(H):
        cnt = sum(1 for c in range(W) if grid[r][c] == 8)
        if cnt and (best is None or cnt > best[0]):
            best = (cnt, 'row', r)

    if best is None:
        return None
    return best[1], best[2]


def _dot_color(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    for v, n in counts.items():
        if v not in (bg, 8) and n > 0:
            return v, bg
    return None, bg


def infer_T(input_grid):
    """Infer the latent transformation mask {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}

    wall = _find_wall(input_grid)
    if wall is None:
        return T
    orient, idx = wall

    dot, bg = _dot_color(input_grid)
    if dot is None:
        return T

    # 1) every existing dot is erased (set to background)
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == dot:
                T[(r, c)] = bg

    # 2) for each wall cell holding an 8, project a single dot adjacent on
    #    each side that has at least one dot along that line position.
    if orient == 'col':
        c = idx
        for r in range(H):
            if input_grid[r][c] != 8:
                continue
            # left side
            if any(input_grid[r][cc] == dot for cc in range(0, c)) and c - 1 >= 0:
                T[(r, c - 1)] = dot
            # right side
            if any(input_grid[r][cc] == dot for cc in range(c + 1, W)) and c + 1 < W:
                T[(r, c + 1)] = dot
    else:  # row wall
        r = idx
        for c in range(W):
            if input_grid[r][c] != 8:
                continue
            # above
            if any(input_grid[rr][c] == dot for rr in range(0, r)) and r - 1 >= 0:
                T[(r - 1, c)] = dot
            # below
            if any(input_grid[rr][c] == dot for rr in range(r + 1, H)) and r + 1 < H:
                T[(r + 1, c)] = dot

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
