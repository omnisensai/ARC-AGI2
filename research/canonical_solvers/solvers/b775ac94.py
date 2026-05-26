from collections import defaultdict


def _components(grid):
    """8-connected components of all non-zero cells."""
    H, W = len(grid), len(grid[0])
    pts = {(r, c): grid[r][c]
           for r in range(H) for c in range(W) if grid[r][c] != 0}
    seen, comps = set(), []
    for start in pts:
        if start in seen:
            continue
        stack, comp = [start], []
        while stack:
            p = stack.pop()
            if p in seen or p not in pts:
                continue
            seen.add(p)
            comp.append(p)
            r, c = p
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr or dc:
                        stack.append((r + dr, c + dc))
        comps.append(comp)
    return pts, comps


def infer_T(input_grid):
    """Latent mask T: dict {(r,c): color} of cells to overwrite.

    Each object is a connected blob in one 'body' color plus 1-3 foreign
    'marker' cells sitting at offsets (dr,dc) in {-1,0,1} around an 'anchor'
    (the body-color cell adjacent to the markers). Each marker reflects the
    whole body across the implied axis/axes and recolors it to the marker
    color; markers at (dr,!=0) flip rows about row-line anchor+dr/2, markers
    at (!=0,dc) flip cols about col-line anchor+dc/2.
    """
    pts, comps = _components(input_grid)
    T = {}
    for comp in comps:
        # body color = most frequent color in component
        ccount = defaultdict(int)
        for p in comp:
            ccount[pts[p]] += 1
        body_color = max(ccount, key=lambda k: (ccount[k], -k))
        body = [p for p in comp if pts[p] == body_color]
        markers = [p for p in comp if pts[p] != body_color]
        if not markers:
            continue
        # anchor = body cell whose offsets to every marker lie in {-1,0,1}
        anchor = None
        for (br, bc) in body:
            ok = True
            for (mr, mc) in markers:
                if abs(mr - br) > 1 or abs(mc - bc) > 1:
                    ok = False
                    break
            if ok:
                anchor = (br, bc)
                break
        if anchor is None:
            continue
        ar, ac = anchor
        for (mr, mc) in markers:
            mcolor = pts[(mr, mc)]
            dr, dc = mr - ar, mc - ac
            for (r, c) in body:
                nr = (2 * ar + dr - r) if dr != 0 else r
                nc = (2 * ac + dc - c) if dc != 0 else c
                T[(nr, nc)] = mcolor
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
