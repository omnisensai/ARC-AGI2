from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    border = [(r, c) for r in range(H) for c in range(W)
              if g[r][c] != bg and (r in (0, H - 1) or c in (0, W - 1))]
    sr, sc = border[0]; S = g[sr][sc]
    d = (1, 0) if sr == 0 else (-1, 0) if sr == H - 1 else (0, 1) if sc == 0 else (0, -1)
    pos = (sr, sc); seen = {pos}; last = pos
    for _ in range(H * W * 2):
        nr, nc = pos[0] + d[0], pos[1] + d[1]
        if not (0 <= nr < H and 0 <= nc < W):
            break
        if g[nr][nc] != bg:
            perps = [(1, 0), (-1, 0)] if d[0] == 0 else [(0, 1), (0, -1)]
            opens = [e for e in perps
                     if 0 <= pos[0] + e[0] < H and 0 <= pos[1] + e[1] < W
                     and g[pos[0] + e[0]][pos[1] + e[1]] == bg
                     and (pos[0] + e[0], pos[1] + e[1]) not in seen]
            if len(opens) == 1:
                d = opens[0]; continue
            break
        if (nr, nc) in seen:
            break
        pos = (nr, nc); seen.add(pos); last = pos
    T = {}
    if last != (sr, sc):
        T[(sr, sc)] = bg          # the ball leaves the entrance (no trail)
        T[last] = S               # and comes to rest at the dead end
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
