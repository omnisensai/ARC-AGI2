"""Canonical latent-T solver for ARC puzzle 212895b5.

Rule (same-size grid; background 0, scattered 5 markers, one 3x3 block of 8):
  The 8-block radiates a figure made of color-4 "staircase" rays and color-2
  diagonal rays.

  * Color-2 diagonal rays: from each of the 4 block corners, step diagonally
    outward, painting empty cells 2. A ray stops when it lands on a 5, or when
    it passes through a "5-gate" (the cell has a 5 on BOTH of its
    forward-orthogonal flanks) -- that gated cell is painted, then the ray ends.

  * Color-4 staircase rays: from the center of each block side, a ray heads
    straight out one step then bends 45 degrees (clockwise: UP->up-right,
    RIGHT->down-right, DOWN->down-left, LEFT->up-left) and climbs as a 2-tread /
    2-riser staircase, painting empty cells 4. It stops the moment the next path
    cell is a 5 or leaves the grid.

infer_T computes the latent change-mask {(r,c): color}; apply_T overlays it.
"""


def _find_block(g):
    H, W = len(g), len(g[0])
    for r in range(H):
        for c in range(W):
            if g[r][c] == 8:
                return r, c
    return None


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    g = input_grid

    def inb(r, c):
        return 0 <= r < H and 0 <= c < W

    blk = _find_block(g)
    if blk is None:
        return {}
    br, bc = blk            # top-left of the 3x3 block of 8s
    cr, cc = br + 1, bc + 1  # block center

    twos = set()
    fours = set()

    # --- color-2 diagonal rays from the four block corners ---
    corners = [
        (br - 1, bc - 1, -1, -1),
        (br - 1, bc + 3, -1, 1),
        (br + 3, bc - 1, 1, -1),
        (br + 3, bc + 3, 1, 1),
    ]
    for sr, sc, dr, dc in corners:
        r, c = sr, sc
        while inb(r, c) and g[r][c] != 5:
            twos.add((r, c))
            # 5-gate: 5 on both forward-orthogonal flanks -> paint then stop
            f1 = (r + dr, c)
            f2 = (r, c + dc)
            g1 = inb(*f1) and g[f1[0]][f1[1]] == 5
            g2 = inb(*f2) and g[f2[0]][f2[1]] == 5
            if g1 and g2:
                break
            r += dr
            c += dc

    # --- color-4 staircase rays from the four block side-centers ---
    sides = {
        "UP": ((br - 1, cc), (-1, 0), (0, 1)),
        "DN": ((br + 3, cc), (1, 0), (0, -1)),
        "LF": ((cr, bc - 1), (0, -1), (-1, 0)),
        "RT": ((cr, bc + 3), (0, 1), (1, 0)),
    }
    steps = max(H, W) + 2
    for start, odir, lat in sides.values():
        # build the staircase path: start, +odir, then repeat (lat,lat, odir,odir)
        path = [start]
        r, c = start
        r += odir[0]
        c += odir[1]
        path.append((r, c))
        for _ in range(steps):
            for _ in range(2):
                r += lat[0]
                c += lat[1]
                path.append((r, c))
            for _ in range(2):
                r += odir[0]
                c += odir[1]
                path.append((r, c))
        for r, c in path:
            if not inb(r, c):
                break
            if g[r][c] == 5:
                break
            fours.add((r, c))

    # latent transformation mask: 2s first, 4s override where they coincide
    T = {}
    for (r, c) in twos:
        if g[r][c] == 0:
            T[(r, c)] = 2
    for (r, c) in fours:
        if g[r][c] in (0,):  # only paint empty cells
            T[(r, c)] = 4
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
