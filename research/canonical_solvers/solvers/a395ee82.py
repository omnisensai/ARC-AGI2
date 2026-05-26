import math
from collections import Counter


def _components(grid, bg, H, W):
    """8-connected components of all non-background cells."""
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W) or grid[rr][cc] == bg:
                        continue
                    seen.add((rr, cc))
                    comp.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            stack.append((rr + dr, cc + dc))
                comps.append(comp)
    return comps


def infer_T(input_grid):
    """
    Structure: one multi-cell connected blob = the TEMPLATE shape (color tcol),
    plus several single-cell markers forming a low-res LAYOUT MAP. In the map,
    exactly one marker shares the template color (the map CENTER); the rest are
    a single other color (sat color). The layout map is a schematic: each lattice
    step (spacing = gcd of marker offsets) corresponds to one template-sized step
    in the output. The template's original position becomes the center stamp,
    recolored to the satellite color; every satellite marker becomes a template
    stamp in the template color, offset by unit*template-bbox. The layout map
    markers themselves are erased.
    """
    H, W = len(input_grid), len(input_grid[0])
    bg = Counter(v for row in input_grid for v in row).most_common(1)[0][0]
    comps = _components(input_grid, bg, H, W)
    if not comps:
        return {}
    big = max(comps, key=len)
    singles = [c[0] for c in comps if len(c) == 1]
    tcol = input_grid[big[0][0]][big[0][1]]
    rs = [r for r, c in big]
    cs = [c for r, c in big]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    th = r1 - r0 + 1
    tw = c1 - c0 + 1
    pat = [(r - r0, c - c0) for r, c in big]
    centers = [(r, c) for r, c in singles if input_grid[r][c] == tcol]
    sats = [(r, c) for r, c in singles if input_grid[r][c] != tcol]
    if not centers or not sats:
        return {}
    scol = input_grid[sats[0][0]][sats[0][1]]
    cen = centers[0]
    offs = [(r - cen[0], c - cen[1]) for r, c in sats]
    sp = 0
    for o in offs:
        for x in o:
            if x != 0:
                sp = math.gcd(sp, abs(x))
    if sp == 0:
        sp = 1

    T = {}
    # erase the layout-map markers (center + satellites)
    for (r, c) in singles:
        T[(r, c)] = bg
    # center stamp: template's original location, recolored to satellite color
    for (pr, pc) in pat:
        T[(r0 + pr, c0 + pc)] = scol
    # satellite stamps: template color, offset by unit * template bbox
    for (dr, dc) in offs:
        ur = dr // sp
        uc = dc // sp
        br = r0 + ur * th
        bc = c0 + uc * tw
        for (pr, pc) in pat:
            rr = br + pr
            cc = bc + pc
            if 0 <= rr < H and 0 <= cc < W:
                T[(rr, cc)] = tcol
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
