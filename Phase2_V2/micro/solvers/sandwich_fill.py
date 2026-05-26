from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    by_color = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg:
                by_color.setdefault(g[r][c], []).append((r, c))
    T = {}
    for col, pts in by_color.items():
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                (r1, c1), (r2, c2) = pts[i], pts[j]
                dr, dc = r2 - r1, c2 - c1
                if not (dr == 0 or dc == 0 or abs(dr) == abs(dc)):
                    continue
                steps = max(abs(dr), abs(dc))
                if steps < 2:
                    continue
                sr = (dr > 0) - (dr < 0); sc = (dc > 0) - (dc < 0)
                between = [(r1 + sr * k, c1 + sc * k) for k in range(1, steps)]
                if all(g[r][c] == bg for (r, c) in between):
                    for (r, c) in between:
                        T[(r, c)] = col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
