from collections import Counter


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def infer_T(g):
    H = len(g)
    W = len(g[0])

    cnt = Counter(v for row in g for v in row)
    frame = cnt.most_common(1)[0][0]

    border = find_border_color(g, frame, H, W)
    T = {}

    if border is None:
        return T

    for cells in components(g, border, H, W):
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]

        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)

        # Interior of the detected box/frame.
        ir0, ir1 = r0 + 1, r1 - 1
        ic0, ic1 = c0 + 1, c1 - 1

        if ir0 <= ir1 and ic0 <= ic1:
            T.update(repair_region(g, ir0, ir1, ic0, ic1))

    return T


def find_border_color(g, frame, H, W):
    cnt = Counter(v for row in g for v in row)

    best_color = None
    best_span = -1

    # Search all non-frame colors. Do not stop at the first one.
    for color in cnt:
        if color == frame:
            continue

        for cells in components(g, color, H, W):
            if not cells:
                continue

            rs = [r for r, c in cells]
            cs = [c for r, c in cells]

            # True bounding-box area.
            span = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)

            if span > best_span:
                best_span = span
                best_color = color

    return best_color


def components(g, color, H, W):
    seen = [[False for _ in range(W)] for _ in range(H)]
    comps = []

    # 8-connected components.
    dirs = [
        (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (1, -1), (-1, 1), (-1, -1),
    ]

    for r in range(H):
        for c in range(W):
            if seen[r][c] or g[r][c] != color:
                continue

            stack = [(r, c)]
            cells = []

            while stack:
                rr, cc = stack.pop()

                if rr < 0 or rr >= H or cc < 0 or cc >= W:
                    continue
                if seen[rr][cc] or g[rr][cc] != color:
                    continue

                seen[rr][cc] = True
                cells.append((rr, cc))

                for dr, dc in dirs:
                    stack.append((rr + dr, cc + dc))

            comps.append(cells)

    return comps


def repair_region(g, r0, r1, c0, c1):
    sub = [
        [g[r][c] for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]

    h = len(sub)
    w = len(sub[0])

    # Detect the repeating period along the longer axis.
    # The shorter axis is treated as one full tile dimension.
    if w >= h:
        row_sequences = [sub[r] for r in range(h)]
        pc = period_along(row_sequences, w)
        pr = h
    else:
        col_sequences = [
            [sub[r][c] for r in range(h)]
            for c in range(w)
        ]
        pr = period_along(col_sequences, h)
        pc = w

    T = {}

    for ph_r in range(pr):
        for ph_c in range(pc):
            vals = []

            for rr in range(ph_r, h, pr):
                for cc in range(ph_c, w, pc):
                    vals.append(sub[rr][cc])

            if not vals:
                continue

            target = Counter(vals).most_common(1)[0][0]

            for rr in range(ph_r, h, pr):
                for cc in range(ph_c, w, pc):
                    if sub[rr][cc] != target:
                        T[(r0 + rr, c0 + cc)] = target

    return T


def period_along(sequences, n):
    if n < 2:
        return n

    def score(p):
        agree = 0
        total = 0

        for seq in sequences:
            for phase in range(p):
                vals = [seq[i] for i in range(phase, n, p)]

                if not vals:
                    continue

                agree += Counter(vals).most_common(1)[0][1]
                total += len(vals)

        return agree / total if total else 0

    best_score = -1

    for p in range(1, n // 2 + 1):
        s = score(p)
        if s > best_score:
            best_score = s

    # If no repeated periodic explanation is strong enough,
    # treat the whole axis as non-periodic.
    if best_score < 0.75:
        return n

    # Return the smallest equally-good period.
    for p in range(1, n // 2 + 1):
        if score(p) >= best_score - 1e-9:
            return p

    return n
