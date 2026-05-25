from collections import Counter


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def _components(g, color, H, W):
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == color and not seen[r][c]:
                st = [(r, c)]
                cells = []
                while st:
                    a, b = st.pop()
                    if a < 0 or a >= H or b < 0 or b >= W or seen[a][b] or g[a][b] != color:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        st.append((a + da, b + db))
                comps.append(cells)
    return comps


def _period_along(seqs, n):
    # seqs: sequences (each length n) sampled along the candidate periodic axis.
    # Return the smallest period p (>=1, repeating at least twice so p<=n//2)
    # whose per-phase consensus best explains the data; else period = n (no
    # genuine repetition along this axis).
    if n < 2:
        return n

    def score(p):
        ag = 0
        tot = 0
        for seq in seqs:
            for ph in range(p):
                col = [seq[i] for i in range(ph, n, p)]
                if not col:
                    continue
                ag += Counter(col).most_common(1)[0][1]
                tot += len(col)
        return ag / tot if tot else 0

    bestsc = -1
    for p in range(1, n // 2 + 1):
        s = score(p)
        if s > bestsc + 1e-9:
            bestsc = s
    if bestsc < 0.75:
        return n
    for p in range(1, n // 2 + 1):
        if score(p) >= bestsc - 1e-9:
            return p
    return n


def _repair_region(g, r0, r1, c0, c1):
    # Repair the periodic pattern inside a box interior: detect the period along
    # the longer axis (the shorter axis is treated as a single tile), then set
    # every cell to the per-phase consensus value of its (pr, pc) tile.
    sub = [[g[r][c] for c in range(c0, c1 + 1)] for r in range(r0, r1 + 1)]
    h = len(sub)
    w = len(sub[0])
    if w >= h:
        rows_seqs = [sub[r] for r in range(h)]
        pc = _period_along(rows_seqs, w)
        pr = h
    else:
        cols_seqs = [[sub[r][c] for r in range(h)] for c in range(w)]
        pr = _period_along(cols_seqs, h)
        pc = w
    changes = {}
    for ph_r in range(pr):
        for ph_c in range(pc):
            vals = []
            for r in range(ph_r, h, pr):
                for c in range(ph_c, w, pc):
                    vals.append(sub[r][c])
            if not vals:
                continue
            val = Counter(vals).most_common(1)[0][0]
            for r in range(ph_r, h, pr):
                for c in range(ph_c, w, pc):
                    if sub[r][c] != val:
                        changes[(r0 + r, c0 + c)] = val
    return changes


def infer_T(g):
    H = len(g)
    W = len(g[0])
    cnt = Counter(v for row in g for v in row)
    frame = cnt.most_common(1)[0][0]
    # Box-border color: the non-frame color whose connected component spans the
    # largest bounding box (the rectangular box frames).
    border = None
    bestspan = -1
    for col, _ in cnt.most_common():
        if col == frame:
            continue
        comps = _components(g, col, H, W)
        for cells in comps:
            rs = [a for a, b in cells]
            cs = [b for a, b in cells]
            span = (max(rs) - min(rs)) * (max(cs) - min(cs))
            if span > bestspan:
                bestspan = span
                border = col
        if border is not None:
            break
    T = {}
    if border is None:
        return T
    for cells in _components(g, border, H, W):
        rs = [a for a, b in cells]
        cs = [b for a, b in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        ir0, ir1, ic0, ic1 = r0 + 1, r1 - 1, c0 + 1, c1 - 1
        if ir1 < ir0 or ic1 < ic0:
            continue
        T.update(_repair_region(g, ir0, ir1, ic0, ic1))
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out
