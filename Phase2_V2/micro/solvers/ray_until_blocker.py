from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    border = [(r, c) for r in range(H) for c in range(W)
              if g[r][c] != bg and (r in (0, H - 1) or c in (0, W - 1))]
    r, c = border[0]
    col = g[r][c]
    if r == 0:
        dr, dc = 1, 0
    elif r == H - 1:
        dr, dc = -1, 0
    elif c == 0:
        dr, dc = 0, 1
    else:
        dr, dc = 0, -1
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
