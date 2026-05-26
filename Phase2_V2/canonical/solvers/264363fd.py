from collections import Counter


def _bg(g):
    c = Counter(v for row in g for v in row)
    return c.most_common(1)[0][0]


def _components(g, bgc):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    out = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bgc and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if a < 0 or b < 0 or a >= H or b >= W or seen[a][b] or g[a][b] == bgc:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((a + dr, b + dc))
                out.append(cells)
    return out


def infer_T(input_grid):
    """Latent mask {(r,c): color}.

    Structure: a background, several large solid-color rectangles each holding
    one or more single 'marker' cells, plus one small isolated 'key' object.
    The key is a cross/diamond stamp whose geometric center marks the marker
    position; its longer axis (distance from center to the key's bounding-box
    edge) tells which cardinal direction(s) get a full line drawn through the
    marker, spanning the entire rectangle. The local key pattern is stamped at
    each marker, and the key itself is erased to background.
    """
    g = input_grid
    bgc = _bg(g)
    comps = _components(g, bgc)
    if not comps:
        return {}
    key = min(comps, key=len)
    rects = [c for c in comps if c is not key]

    # key geometry
    krs = [r for r, c in key]
    kcs = [c for r, c in key]
    kr0, kr1, kc0, kc1 = min(krs), max(krs), min(kcs), max(kcs)
    kcr = (kr0 + kr1) // 2
    kcc = (kc0 + kc1) // 2
    kset = {(r, c): g[r][c] for r, c in key}
    rel = {(r - kcr, c - kcc): v for (r, c), v in kset.items()}
    center_color = kset.get((kcr, kcc))

    # arm distances from center to key bounding-box edges
    vdist = min(kcr - kr0, kr1 - kcr)
    hdist = min(kcc - kc0, kc1 - kcc)
    vcolor = kset.get((kr0, kcc))  # line color for vertical extension
    hcolor = kset.get((kcr, kc0))  # line color for horizontal extension
    do_vert = vdist >= hdist and vdist > 0
    do_horz = hdist >= vdist and hdist > 0

    T = {}
    # the key is consumed once interpreted
    for (r, c) in key:
        T[(r, c)] = bgc

    for cells in rects:
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        rr0, rr1, cc0, cc1 = min(rs), max(rs), min(cs), max(cs)
        cnt = Counter(g[r][c] for r, c in cells)
        dom = cnt.most_common(1)[0][0]
        markers = [(r, c) for r, c in cells if g[r][c] != dom]
        for (mr, mc) in markers:
            # full lines through the marker spanning the rectangle
            if do_vert and cc0 <= mc <= cc1:
                for r in range(rr0, rr1 + 1):
                    T[(r, mc)] = vcolor
            if do_horz and rr0 <= mr <= rr1:
                for c in range(cc0, cc1 + 1):
                    T[(mr, c)] = hcolor
            # stamp the local key pattern (clipped to the rectangle)
            for (dr, dc), v in rel.items():
                r = mr + dr
                c = mc + dc
                if rr0 <= r <= rr1 and cc0 <= c <= cc1:
                    T[(r, c)] = v
            # center keeps the marker color
            T[(mr, mc)] = center_color if center_color is not None else g[mr][mc]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
