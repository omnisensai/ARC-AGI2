from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    dirs = {(0, 0): (1, 1), (0, W - 1): (1, -1),
            (H - 1, 0): (-1, 1), (H - 1, W - 1): (-1, -1)}
    r, c = next((p for p in dirs if g[p[0]][p[1]] != bg))
    col = g[r][c]
    dr, dc = dirs[(r, c)]
    T = {}
    rr, cc = r + dr, c + dc
    while 0 <= rr < H and 0 <= cc < W and g[rr][cc] == bg:
        T[(rr, cc)] = col
        rr += dr
        cc += dc
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
