from collections import deque


def infer_T(input_grid):
    """Infer the latent overwrite mask {(r,c): color}.

    Structure: one 'legend' component contains both color-1 cells (the paint
    shape) and color-2 cells (markers). Elsewhere the grid holds solid s x s
    squares of color 2 (targets). Each target square corresponds to a legend
    marker; matching a group of target squares to all legend markers (at a
    consistent scale s and translation) lets us stamp a scaled (s x s blocks)
    copy of the legend's 1-shape, aligned by the markers.
    """
    H, W = len(input_grid), len(input_grid[0])

    def components(colorset):
        seen = [[False] * W for _ in range(H)]
        comps = []
        for r in range(H):
            for c in range(W):
                if input_grid[r][c] in colorset and not seen[r][c]:
                    q = deque([(r, c)]); seen[r][c] = True; cells = []
                    while q:
                        a, b = q.popleft(); cells.append((a, b))
                        for dr in (-1, 0, 1):
                            for dc in (-1, 0, 1):
                                if dr == 0 and dc == 0:
                                    continue
                                na, nb = a + dr, b + dc
                                if (0 <= na < H and 0 <= nb < W and not seen[na][nb]
                                        and input_grid[na][nb] in colorset):
                                    seen[na][nb] = True; q.append((na, nb))
                    comps.append(cells)
        return comps

    comps = components({1, 2})

    # Legend: the component containing both 1 and 2.
    legend = None
    for cc in comps:
        cols = set(input_grid[r][c] for r, c in cc)
        if 1 in cols and 2 in cols:
            legend = cc
            break

    T = {}
    if legend is None:
        return T

    lr0 = min(r for r, _ in legend)
    lc0 = min(c for _, c in legend)
    markers = [(r - lr0, c - lc0) for r, c in legend if input_grid[r][c] == 2]
    paints = [(r - lr0, c - lc0) for r, c in legend if input_grid[r][c] == 1]
    M = len(markers)
    if M == 0:
        return T

    # Target blocks: pure-2 solid squares.
    targets = []
    for cc in comps:
        cols = set(input_grid[r][c] for r, c in cc)
        if cols == {2}:
            rs = [r for r, _ in cc]; cs = [c for _, c in cc]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            h, w = r1 - r0 + 1, c1 - c0 + 1
            if h == w and len(cc) == h * w:
                targets.append({'r0': r0, 'c0': c0, 's': h, 'used': False})

    def find_block(r0, c0, s):
        for t in targets:
            if not t['used'] and t['s'] == s and t['r0'] == r0 and t['c0'] == c0:
                return t
        return None

    for anchor in targets:
        if anchor['used']:
            continue
        s = anchor['s']
        for (mr, mc) in markers:
            # Hypothesis: this legend marker maps onto the anchor block.
            br0 = anchor['r0'] - mr * s
            bc0 = anchor['c0'] - mc * s
            group = []
            ok = True
            for (gmr, gmc) in markers:
                blk = find_block(br0 + gmr * s, bc0 + gmc * s, s)
                if blk is None:
                    ok = False
                    break
                group.append(blk)
            if ok and len(group) == M:
                for (pr, pc) in paints:
                    tr = br0 + pr * s
                    tc = bc0 + pc * s
                    for i in range(s):
                        for j in range(s):
                            rr, ccc = tr + i, tc + j
                            if 0 <= rr < H and 0 <= ccc < W:
                                T[(rr, ccc)] = 1
                for blk in group:
                    blk['used'] = True
                break

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
