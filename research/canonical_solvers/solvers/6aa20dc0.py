from collections import Counter


def _bg(g):
    return Counter(v for row in g for v in row).most_common(1)[0][0]


def _components(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                seen[r][c] = True
                while stack:
                    rr, cc = stack.pop()
                    cells.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = rr + dr, cc + dc
                            if (0 <= nr < H and 0 <= nc < W
                                    and g[nr][nc] != bg and not seen[nr][nc]):
                                seen[nr][nc] = True
                                stack.append((nr, nc))
                comps.append(cells)
    return comps


def _all_transforms(g3):
    def rot(g):
        n = len(g)
        return [[g[n - 1 - c][r] for c in range(n)] for r in range(n)]

    def fliph(g):
        return [row[::-1] for row in g]

    res = []
    cur = g3
    for _ in range(4):
        res.append(cur)
        res.append(fliph(cur))
        cur = rot(cur)
    return res


def infer_T(input_grid):
    """Latent mask: dict {(r,c): new_color} of cells to overwrite.

    Structure of the puzzle: a 3x3 multicolor 'key' template holds a fill
    color (its majority color) plus two anchor colors sitting at two of its
    corners. Elsewhere appear pairs of solid mono blobs, one per anchor color,
    placed at two diagonally-opposite corners of a 3x3 super-grid (each grid
    cell = one blob's size). We pick the dihedral orientation of the key whose
    anchor colors land on the two blob corners, then stamp the key's fill
    pattern (scaled to blob size) into the super-grid, painting fill-color
    cells and leaving holes/anchors untouched.
    """
    gi = input_grid
    bg = _bg(gi)
    H, W = len(gi), len(gi[0])
    comps = _components(gi, bg)

    key = None
    blobs = []
    for cells in comps:
        cols = set(gi[r][c] for r, c in cells)
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        if (len(cols) >= 3 and max(rs) - min(rs) == 2
                and max(cs) - min(cs) == 2):
            key = (cells, min(rs), min(cs))
        else:
            blobs.append((cells, next(iter(cols))))

    T = {}
    if key is None:
        return T

    cells, kr, kc = key
    kgrid = [[bg] * 3 for _ in range(3)]
    for r, c in cells:
        kgrid[r - kr][c - kc] = gi[r][c]
    fill = Counter(gi[r][c] for r, c in cells).most_common(1)[0][0]

    anchor_colors = set()
    for r in range(3):
        for c in range(3):
            v = kgrid[r][c]
            if v != bg and v != fill:
                anchor_colors.add(v)

    # bounding boxes of all mono blobs
    bbox = []
    for bcells, bcol in blobs:
        rs = [r for r, c in bcells]
        cs = [c for r, c in bcells]
        bbox.append((bcol, min(rs), min(cs), max(rs), max(cs)))

    transforms = _all_transforms(kgrid)
    used = [False] * len(bbox)

    for i in range(len(bbox)):
        if used[i]:
            continue
        col_i, r0, c0, r1, c1 = bbox[i]
        bh = r1 - r0 + 1
        bw = c1 - c0 + 1

        # find the partner blob of the other anchor color completing a 3x3
        # super-grid of equal-sized blocks
        best = None
        for j in range(len(bbox)):
            if j == i or used[j]:
                continue
            col_j, R0, C0, R1, C1 = bbox[j]
            if col_j == col_i:
                continue
            if {col_i, col_j} != anchor_colors:
                continue
            gr0, gr1 = min(r0, R0), max(r1, R1)
            gc0, gc1 = min(c0, C0), max(c1, C1)
            if (gr1 - gr0 + 1) == 3 * bh and (gc1 - gc0 + 1) == 3 * bw:
                dist = abs(r0 - R0) + abs(c0 - C0)
                if best is None or dist < best[0]:
                    best = (dist, j, gr0, gc0, col_j, R0, C0)
        if best is None:
            continue

        _, j, gr0, gc0, col_j, R0, C0 = best
        used[i] = used[j] = True

        def blockpos(r, c):
            return ((r - gr0) // bh, (c - gc0) // bw)

        pi = blockpos(r0, c0)
        pj = blockpos(R0, C0)

        # choose key orientation putting each anchor color at its blob corner
        chosen = None
        for tg in transforms:
            posi = posj = None
            for rr in range(3):
                for cc in range(3):
                    if tg[rr][cc] == col_i:
                        posi = (rr, cc)
                    if tg[rr][cc] == col_j:
                        posj = (rr, cc)
            if posi == pi and posj == pj:
                chosen = tg
                break
        if chosen is None:
            continue

        # stamp fill-color blocks of the oriented key into the mask
        for br in range(3):
            for bc in range(3):
                v = chosen[br][bc]
                if v == bg or v in anchor_colors:
                    continue
                rr0 = gr0 + br * bh
                cc0 = gc0 + bc * bw
                for dr in range(bh):
                    for dc in range(bw):
                        rr, cc = rr0 + dr, cc0 + dc
                        if 0 <= rr < H and 0 <= cc < W:
                            T[(rr, cc)] = fill
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
