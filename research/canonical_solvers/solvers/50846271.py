"""Canonical solver for ARC puzzle 50846271.

Rule
----
On a noisy 0/5 background there are several incomplete plus/cross shapes drawn in
color 2. Each cross has a center and four axis-aligned arms, but some arm cells
(and sometimes the center) are missing -- they show up as background 5s instead
of 2s. The task completes every cross into a full symmetric plus, painting the
*missing* skeleton cells (those currently 5) with color 8. Cells already 2 stay
2, and 0-background cells are never touched.

The arm half-length M of the crosses is uniform within a grid, so it is taken as
the maximum arm reach observed across all crosses.

Canonical form: infer_T builds the latent mask {(r,c): 8} of cells to repaint,
apply_T copies the input and overwrites only those masked cells.
"""

from collections import deque, Counter


def infer_T(g):
    H, W = len(g), len(g[0])

    def inb(r, c):
        return 0 <= r < H and 0 <= c < W

    twos = [(r, c) for r in range(H) for c in range(W) if g[r][c] == 2]

    # Cluster the 2-cells into individual crosses. Two 2-cells join if they lie
    # on the same row/column within distance 4 (tolerating the gaps left by the
    # missing arm cells) or are within a 2-cell Chebyshev neighbourhood.
    seen = set()
    comps = []
    for pt in twos:
        if pt in seen:
            continue
        q = deque([pt])
        seen.add(pt)
        comp = []
        while q:
            x, y = q.popleft()
            comp.append((x, y))
            for (a, b) in twos:
                if (a, b) in seen:
                    continue
                if ((a == x and abs(b - y) <= 4) or
                        (b == y and abs(a - x) <= 4) or
                        (abs(a - x) <= 2 and abs(b - y) <= 2)):
                    seen.add((a, b))
                    q.append((a, b))
        comps.append(comp)

    def pick(counts, lo, hi):
        # The center row (col) is the line carrying the most 2-cells; if there is
        # no clear dominant line, fall back to the middle of the observed span.
        best = counts.most_common()
        if best and best[0][1] >= 2:
            top = [k for k, v in best if v == best[0][1]]
            if len(top) == 1:
                return top[0]
        return (lo + hi) // 2

    centers = []
    m_vals = []
    for comp in comps:
        rs = [r for r, c in comp]
        cs = [c for r, c in comp]
        cr = pick(Counter(rs), min(rs), max(rs))
        ccol = pick(Counter(cs), min(cs), max(cs))
        m = max(max(abs(r - cr) for r, c in comp),
                max(abs(c - ccol) for r, c in comp))
        centers.append((cr, ccol))
        m_vals.append(m)

    m_global = max(m_vals) if m_vals else 0

    # Latent transformation mask: skeleton cells that are currently background 5.
    T = {}
    for (cr, ccol) in centers:
        skel = {(cr, ccol)}
        for step in range(1, m_global + 1):
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                skel.add((cr + dr * step, ccol + dc * step))
        for (r, c) in skel:
            if inb(r, c) and g[r][c] == 5:
                T[(r, c)] = 8
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
