"""Canonical latent-T solver for ARC puzzle da515329.

Rule (inferred from input structure only):
  The input contains a single small plus/cross of color 8 with an empty center
  cell and four equal-length arms (length L) pointing up/down/left/right.
  Each arm seeds a turtle that draws an expanding square spiral, all four
  turning clockwise. The four interleaved spirals (corridor width 1) tile the
  grid; the spiral lines are color 8, and the center cell stays empty.

  Per turtle: go straight along the arm direction to radius max(L,2), then for
  ring k = 0,1,2,...: turn clockwise; if L>2 there is a staircase "jog" of
  (L-2) cells: travel to perpendicular radius (2+2k), jog (L-2) cells clockwise,
  then continue to radius (2+2k)+max(L,2); if L<=2 the side is a single straight
  leg to radius (2+2k)+max(L,2). The ideal infinite path is intersected with the
  grid (cells outside are clipped).

infer_T returns the latent mask: the set of cells to paint 8 (the spiral).
apply_T copies the input and overwrites only the masked cells.
"""


def _find_cross(grid):
    H, W = len(grid), len(grid[0])
    cells = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == 8]
    if not cells:
        return None
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    cr = (min(rs) + max(rs)) // 2
    cc = (min(cs) + max(cs)) // 2
    cset = set(cells)
    # arm length L: count consecutive 8s straight up from the center
    L = 0
    r, c = cr - 1, cc
    while (r, c) in cset:
        L += 1
        r -= 1
    return (cr, cc), L, H, W


def _cw(d):
    # clockwise rotation in image coords (row down, col right)
    return (d[1], -d[0])


def _turtle_corners(L, cr, cc, arm_dir, H, W):
    """Corner waypoints of one spiral turtle (ideal, possibly outside grid)."""
    pts = [(cr, cc)]
    leg0 = max(L, 2)
    r = cr + arm_dir[0] * leg0
    c = cc + arm_dir[1] * leg0
    pts.append((r, c))
    cur = (r, c)
    cdir = arm_dir
    jog = L - 2

    def go(pos, direction, rad):
        pr, pc = pos
        if direction[0] != 0:          # vertical leg -> set target row
            return (cr + direction[0] * rad, pc)
        else:                          # horizontal leg -> set target col
            return (pr, cc + direction[1] * rad)

    for k in range(2 * (H + W) + 8):
        cdir = _cw(cdir)
        prerad = 2 + 2 * k
        finalrad = prerad + max(L, 2)
        if jog > 0:
            mid = go(cur, cdir, prerad)
            pts.append(mid)
            jd = _cw(cdir)
            jp = (mid[0] + jd[0] * jog, mid[1] + jd[1] * jog)
            pts.append(jp)
            end = go(jp, cdir, finalrad)
            pts.append(end)
            cur = end
        else:
            end = go(cur, cdir, finalrad)
            pts.append(end)
            cur = end
        if not (-3 <= cur[0] <= H + 3 and -3 <= cur[1] <= W + 3):
            break
    return pts


def _raster(pts, H, W):
    """Walk all segments cell-by-cell, keeping only in-grid cells."""
    drawn = set()
    cur = pts[0]
    if 0 <= cur[0] < H and 0 <= cur[1] < W:
        drawn.add(cur)
    for nxt in pts[1:]:
        r, c = cur
        tr, tc = nxt
        dr = (tr > r) - (tr < r)
        dc = (tc > c) - (tc < c)
        while (r, c) != (tr, tc):
            r += dr
            c += dc
            if 0 <= r < H and 0 <= c < W:
                drawn.add((r, c))
        cur = nxt
    return drawn


def infer_T(input_grid):
    """Infer the latent transformation mask: cells to paint color 8."""
    H, W = len(input_grid), len(input_grid[0])
    found = _find_cross(input_grid)
    T = {}
    if found is None:
        return T
    (cr, cc), L, _, _ = found
    drawn = set()
    for arm_dir in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
        pts = _turtle_corners(L, cr, cc, arm_dir, H, W)
        drawn |= _raster(pts, H, W)
    drawn.discard((cr, cc))  # center stays empty
    for (r, c) in drawn:
        T[(r, c)] = 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
