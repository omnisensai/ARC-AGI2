"""Canonical solver for ARC puzzle 2dd70a9a.

Rule
----
The grid contains two 2-cell "domino" markers: one colored 3 and one colored 2,
both drawn against a background of 0 with 8s scattered as obstacles. Each domino
lies along an axis (horizontal or vertical). Each marker emits a straight ray of
color 3 from its far end, traveling along its own axis until it is blocked by an
8 (or the grid border), stopping at the last empty cell.

Ray direction along the axis:
  - if exactly one axis-end is immediately blocked by an 8/border, the ray goes
    out the open end;
  - otherwise it heads toward the other marker's position along that axis;
  - if the two markers are exactly aligned on that axis (a tie), the ray copies
    the other marker's chosen direction.

The 3-ray's stopping coordinate defines an elbow line. A single perpendicular
connector (color 3) is drawn from the 3-ray's stop point to that elbow line, and
the 2-ray is extended only as far as the elbow, so the two rays join in an
L/Z-shaped path of 3s. All painted cells become 3 (the original 2 and 3 markers
are preserved).
"""


def _find(g, v):
    return [(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] == v]


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    th = sorted(_find(input_grid, 3))
    tw = sorted(_find(input_grid, 2))
    T = {}
    if len(th) != 2 or len(tw) != 2:
        return T

    th_vert = th[0][1] == th[1][1]
    tw_vert = tw[0][1] == tw[1][1]

    def blocked(r, c):
        if not (0 <= r < H and 0 <= c < W):
            return True
        return input_grid[r][c] == 8

    def axis_dir(dom, vert, other_center):
        """Return ((start_r, start_c, step), neg, pos). start is the first cell
        of the ray (just beyond the domino's chosen end)."""
        if vert:
            lo = (min(dom[0][0], dom[1][0]), dom[0][1])
            hi = (max(dom[0][0], dom[1][0]), dom[0][1])
            neg = (lo[0] - 1, lo[1], (-1, 0))   # up
            pos = (hi[0] + 1, hi[1], (1, 0))    # down
            oth = other_center[0]
            mid = (lo[0] + hi[0]) / 2.0
        else:
            lo = (dom[0][0], min(dom[0][1], dom[1][1]))
            hi = (dom[0][0], max(dom[0][1], dom[1][1]))
            neg = (lo[0], lo[1] - 1, (0, -1))   # left
            pos = (hi[0], hi[1] + 1, (0, 1))    # right
            oth = other_center[1]
            mid = (lo[1] + hi[1]) / 2.0
        neg_blk = blocked(neg[0], neg[1])
        pos_blk = blocked(pos[0], pos[1])
        if neg_blk and not pos_blk:
            chosen = pos
        elif pos_blk and not neg_blk:
            chosen = neg
        else:
            if oth < mid:
                chosen = neg
            elif oth > mid:
                chosen = pos
            else:
                chosen = None
        return chosen, neg, pos

    c3 = ((th[0][0] + th[1][0]) / 2.0, (th[0][1] + th[1][1]) / 2.0)
    c2 = ((tw[0][0] + tw[1][0]) / 2.0, (tw[0][1] + tw[1][1]) / 2.0)

    d3, neg3, pos3 = axis_dir(th, th_vert, c2)
    d2, neg2, pos2 = axis_dir(tw, tw_vert, c3)

    def pick_by_step(step, neg, pos):
        return neg if step[0] < 0 or step[1] < 0 else pos

    if d3 is None and d2 is not None:
        d3 = pick_by_step(d2[2], neg3, pos3)
    if d2 is None and d3 is not None:
        d2 = pick_by_step(d3[2], neg2, pos2)
    if d3 is None or d2 is None:
        return T

    def ray(start, step):
        cells = []
        r, c = start[0], start[1]
        while 0 <= r < H and 0 <= c < W and input_grid[r][c] != 8:
            cells.append((r, c))
            r += step[0]
            c += step[1]
        return cells

    ray3 = ray((d3[0], d3[1]), d3[2])
    ray2 = ray((d2[0], d2[1]), d2[2])
    stop3 = ray3[-1] if ray3 else (d3[0], d3[1])

    cells = set(ray3)
    if th_vert:
        rr = stop3[0]
        col2 = d2[1]
        for (r, c) in ray2:
            cells.add((r, c))
            if r == rr:
                break
        lo, hi = sorted([stop3[1], col2])
        for cc in range(lo, hi + 1):
            cells.add((rr, cc))
    else:
        cc = stop3[1]
        row2 = d2[0]
        for (r, c) in ray2:
            cells.add((r, c))
            if c == cc:
                break
        lo, hi = sorted([stop3[0], row2])
        for rr in range(lo, hi + 1):
            cells.add((rr, cc))

    for cell in cells:
        T[cell] = 3
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
