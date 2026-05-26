"""Canonical solver for ARC puzzle 3ad05f52.

Rule (single transformation):
  The grid is a maze of 8-walls dividing space into rooms. One or more rooms
  hold a single non-background "seed" colour. That colour floods through the
  maze: it passes from room to room only through wall GAPS (a single non-wall
  cell breaking an otherwise solid wall line), and every reachable room is
  filled completely with the seed colour (gap cells included).

  When the flood reaches the surrounding open EXTERIOR (the single largest
  open region) through a gap, it does NOT fill the whole exterior; instead it
  fills the rectangular "band" between the gap it entered through and another
  gap it can connect to (the bounding box of the two gaps, restricted to the
  exterior, when those exterior cells form one connected strip touching both
  gaps). Dead-end pockets that are walled on all sides (the grid edge counting
  as a wall) are ordinary rooms and fill entirely.

infer_T computes the latent mask T = {(r,c): seed_colour} of cells to overwrite;
apply_T copies the input and writes only those cells.
"""


def _neighbors(r, c):
    yield r + 1, c
    yield r - 1, c
    yield r, c + 1
    yield r, c - 1


def infer_T(g):
    H, W = len(g), len(g[0])

    # --- seed colour & seed cells (anything that is not background 0 / wall 8) ---
    seeds = []
    color = None
    for r in range(H):
        for c in range(W):
            v = g[r][c]
            if v != 0 and v != 8:
                seeds.append((r, c))
                color = v
    if color is None:
        return {}

    # --- gap cells: a 0-cell that breaks a wall line (non-0 on two opposite sides) ---
    gap = set()
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0:
                continue
            L = c > 0 and g[r][c - 1] != 0
            R = c < W - 1 and g[r][c + 1] != 0
            U = r > 0 and g[r - 1][c] != 0
            D = r < H - 1 and g[r + 1][c] != 0
            if (L and R) or (U and D):
                gap.add((r, c))

    # --- 0-regions, cut apart by gaps (gaps are connectors, not region members) ---
    region_of = {}
    regions = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == 0 and (r, c) not in gap and (r, c) not in region_of:
                comp = []
                stack = [(r, c)]
                while stack:
                    x = stack.pop()
                    if x in region_of:
                        continue
                    xr, xc = x
                    if not (0 <= xr < H and 0 <= xc < W):
                        continue
                    if g[xr][xc] != 0 or x in gap:
                        continue
                    region_of[x] = len(regions)
                    comp.append(x)
                    for nbr in _neighbors(xr, xc):
                        stack.append(nbr)
                regions.append(comp)

    # exterior = the single largest open region (the surrounding space);
    # every other open region is a room / dead-end pocket.
    if regions:
        ext_id = max(range(len(regions)), key=lambda i: len(regions[i]))
        ext = set(regions[ext_id])
    else:
        ext_id = -1
        ext = set()

    # gaps that border the exterior region
    ext_gaps = []
    for (r, c) in gap:
        for nr, nc in _neighbors(r, c):
            if (nr, nc) in region_of and region_of[(nr, nc)] == ext_id:
                ext_gaps.append((r, c))
                break

    # --- flood the seed colour ---
    filled = set(seeds)
    changed = True
    while changed:
        changed = False
        # 1) free flood through rooms + gaps (everything non-wall except exterior)
        stack = list(filled)
        while stack:
            r, c = stack.pop()
            for nr, nc in _neighbors(r, c):
                if not (0 <= nr < H and 0 <= nc < W):
                    continue
                if g[nr][nc] == 8:
                    continue
                if (nr, nc) in ext:
                    continue
                if (nr, nc) not in filled:
                    filled.add((nr, nc))
                    stack.append((nr, nc))
                    changed = True

        # 2) exterior bands: between a reached exterior-gap and another exterior-gap,
        #    fill their bounding box restricted to exterior, when those exterior cells
        #    form one connected strip adjacent to both gaps.
        reached = [gp for gp in ext_gaps if gp in filled]
        for a in reached:
            for b in ext_gaps:
                if a == b:
                    continue
                r0, r1 = min(a[0], b[0]), max(a[0], b[0])
                c0, c1 = min(a[1], b[1]), max(a[1], b[1])
                cand = set(
                    (rr, cc)
                    for rr in range(r0, r1 + 1)
                    for cc in range(c0, c1 + 1)
                    if (rr, cc) in ext
                )
                if not cand:
                    continue
                a_adj = any((nr, nc) in cand for nr, nc in _neighbors(*a))
                b_adj = any((nr, nc) in cand for nr, nc in _neighbors(*b))
                if not (a_adj and b_adj):
                    continue
                # candidate strip must be connected
                start = next(iter(cand))
                comp = set()
                st = [start]
                while st:
                    x = st.pop()
                    if x in comp:
                        continue
                    comp.add(x)
                    for nr, nc in _neighbors(*x):
                        if (nr, nc) in cand and (nr, nc) not in comp:
                            st.append((nr, nc))
                if len(comp) != len(cand):
                    continue
                for cell in cand:
                    if cell not in filled:
                        filled.add(cell)
                        changed = True

    # latent mask: overwrite each filled cell with the seed colour
    T = {(r, c): color for (r, c) in filled}
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
