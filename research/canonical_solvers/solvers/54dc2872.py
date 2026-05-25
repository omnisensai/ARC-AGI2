from collections import defaultdict


def _components(g, bg=0):
    H, W = len(g), len(g[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg or (r, c) in seen:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                a, b = stack.pop()
                if (a, b) in seen or not (0 <= a < H and 0 <= b < W) or g[a][b] == bg:
                    continue
                seen.add((a, b))
                cells.append((a, b))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((a + dr, b + dc))
            out.append(cells)
    return out


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = 0
    objects = []
    targets = {}
    for cs in _components(input_grid, bg):
        if len(cs) == 1:
            (r, c) = cs[0]
            targets[input_grid[r][c]] = (r, c)
            continue
        cols = defaultdict(list)
        for (r, c) in cs:
            cols[input_grid[r][c]].append((r, c))
        body = max(cols, key=lambda k: len(cols[k]))
        keys = [k for k in cols if k != body]
        if len(keys) != 1 or len(cols[keys[0]]) != 1:
            continue
        key = keys[0]
        objects.append((body, key, cols[key][0], cols[body]))

    T = {}
    for body, key, kp, body_cells in objects:
        if key not in targets:
            continue
        bodyset = set(body_cells)
        dirs = [(dr, dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                if (kp[0] + dr, kp[1] + dc) in bodyset]
        rr = sum(dr for dr, dc in dirs)
        cc = sum(dc for dr, dc in dirs)
        corner = (kp[0] + rr, kp[1] + cc)
        tgt = targets[key]
        off = (tgt[0] - corner[0], tgt[1] - corner[1])
        for (r, c) in body_cells:
            T[(r, c)] = bg
        T[(kp[0], kp[1])] = bg
        for (r, c) in body_cells:
            T[(r + off[0], c + off[1])] = body
        T[(kp[0] + off[0], kp[1] + off[1])] = key
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
