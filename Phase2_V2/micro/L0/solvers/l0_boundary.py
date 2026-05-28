from collections import Counter


def infer_T(g):
    bv = Counter(v for row in g for v in row).most_common(1)[0][0]
    H, W = len(g), len(g[0])
    cells = {(r, c) for r in range(H) for c in range(W) if g[r][c] != bv}
    T = {}
    for (r, c) in cells:
        for (nr, nc) in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if not (0 <= nr < H and 0 <= nc < W) or (nr, nc) not in cells:
                T[(r, c)] = 1                # MARK — this cell is on the 4-boundary
                break
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
