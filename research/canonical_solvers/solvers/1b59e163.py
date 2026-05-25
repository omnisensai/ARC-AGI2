from collections import deque, Counter

def _components(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False]*W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                q = deque([(r, c)]); seen[r][c] = True; comp = []
                while q:
                    rr, cc = q.popleft(); comp.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0: continue
                            nr, nc = rr+dr, cc+dc
                            if 0 <= nr < H and 0 <= nc < W and grid[nr][nc] != bg and not seen[nr][nc]:
                                seen[nr][nc] = True; q.append((nr, nc))
                comps.append(comp)
    return comps

def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = Counter(v for row in input_grid for v in row).most_common(1)[0][0]
    comps = _components(input_grid, bg)

    templates = {}
    lones = []
    for comp in comps:
        if len(comp) == 1:
            r, c = comp[0]
            lones.append((r, c, input_grid[r][c]))
            continue
        colors = Counter(input_grid[r][c] for r, c in comp)
        marker_color = min(colors, key=lambda k: colors[k])
        mr, mc = next((r, c) for r, c in comp if input_grid[r][c] == marker_color)
        rel = [(r-mr, c-mc, input_grid[r][c]) for r, c in comp]
        templates[marker_color] = rel

    T = {}
    for (lr, lc, col) in lones:
        if col in templates:
            for (dr, dc, color) in templates[col]:
                r, c = lr+dr, lc+dc
                if 0 <= r < H and 0 <= c < W:
                    T[(r, c)] = color
    return T, bg

def apply_T(input_grid, T_bg):
    T, bg = T_bg
    H, W = len(input_grid), len(input_grid[0])
    out = [[bg]*W for _ in range(H)]
    for (r, c), color in T.items():
        out[r][c] = color
    return out

def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
