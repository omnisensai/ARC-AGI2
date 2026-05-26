"""Canonical solver for ARC puzzle 60a26a3e.

Rule: The grid contains diamond markers made of four 2-cells arranged
orthogonally around an empty center cell. Whenever two diamond centers share a
row or a column (with no third diamond center between them and only empty cells
in the gap), draw a straight line of color 1 through the empty cells lying
strictly between their two facing tips. Everything else is left untouched.
"""


def _centers(g):
    H, W = len(g), len(g[0])
    cs = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0:
                continue
            nb = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
            if all(0 <= rr < H and 0 <= cc < W and g[rr][cc] == 2 for rr, cc in nb):
                cs.append((r, c))
    return cs


def infer_T(input_grid):
    g = input_grid
    centers = _centers(g)
    cset = set(centers)
    T = {}  # latent mask: {(r, c): new_color}
    for (r, c) in centers:
        for (r2, c2) in centers:
            if (r, c) >= (r2, c2):
                continue
            if r == r2:
                a, b = min(c, c2), max(c, c2)
                # cells strictly between the two facing horizontal tips
                t1, t2 = a + 2, b - 2
                if t1 > t2:
                    continue
                seg = [(r, cc) for cc in range(t1, t2 + 1)]
                if all(g[rr][cc] == 0 for rr, cc in seg) and \
                        not any(rr == r and a < cc < b for (rr, cc) in cset):
                    for cell in seg:
                        T[cell] = 1
            elif c == c2:
                a, b = min(r, r2), max(r, r2)
                t1, t2 = a + 2, b - 2
                if t1 > t2:
                    continue
                seg = [(rr, c) for rr in range(t1, t2 + 1)]
                if all(g[rr][cc] == 0 for rr, cc in seg) and \
                        not any(cc == c and a < rr < b for (rr, cc) in cset):
                    for cell in seg:
                        T[cell] = 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
