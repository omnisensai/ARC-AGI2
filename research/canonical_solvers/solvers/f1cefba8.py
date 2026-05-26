"""Canonical solver for ARC puzzle f1cefba8.

Structure: a rectangular frame (border color) encloses a solid rectangle of a
fill color. The fill rectangle has a few single-cell "bumps" protruding past one
of its clean edges. Each bump marks a cut line perpendicular to that edge:
  - a top/bottom bump (in column cc) marks a vertical cut at column cc
  - a left/right bump (in row rr) marks a horizontal cut at row rr
For each cut line the fill color is drawn across the background outside the frame
and the frame color is drawn across the interior of the clean rectangle; the bump
itself is cleaned back to the frame color.

infer_T returns a latent mask {(r,c): new_color}; apply_T overwrites only those
cells of a copy of the input.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    cnt = {}
    for row in input_grid:
        for v in row:
            cnt[v] = cnt.get(v, 0) + 1
    bg = max(cnt, key=cnt.get)

    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    if not cells:
        return {}
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    fr0, fc0 = min(rs), min(cs)
    frame = input_grid[fr0][fc0]
    others = [v for v in cnt if v not in (bg, frame)]
    if not others:
        return {}
    fill = others[0]

    fset = {(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == fill}
    frs = [r for r, c in fset]
    fcs = [c for r, c in fset]
    a0, b0, c0, e0 = min(frs), max(frs), min(fcs), max(fcs)

    # Largest solid rectangle of fill color = the "clean" interior rectangle.
    best = None
    for a in range(a0, b0 + 1):
        for b in range(a, b0 + 1):
            for c in range(c0, e0 + 1):
                for e in range(c, e0 + 1):
                    if all((r, cc) in fset
                           for r in range(a, b + 1)
                           for cc in range(c, e + 1)):
                        area = (b - a + 1) * (e - c + 1)
                        if best is None or area > best[0]:
                            best = (area, a, b, c, e)
    _, a, b, c, e = best

    bumps = [(r, cc) for (r, cc) in fset if not (a <= r <= b and c <= cc <= e)]

    T = {}
    # Clean every bump back to the frame color.
    for (r, cc) in bumps:
        T[(r, cc)] = frame

    for (r, cc) in bumps:
        if r < a or r > b:
            # top/bottom bump -> vertical cut line at column cc
            for rr in range(H):
                if a <= rr <= b:
                    T[(rr, cc)] = frame
                elif input_grid[rr][cc] == bg:
                    T[(rr, cc)] = fill
        elif cc < c or cc > e:
            # left/right bump -> horizontal cut line at row r
            for ccx in range(W):
                if c <= ccx <= e:
                    T[(r, ccx)] = frame
                elif input_grid[r][ccx] == bg:
                    T[(r, ccx)] = fill
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
