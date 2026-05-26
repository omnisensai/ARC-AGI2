"""Canonical solver for ARC puzzle a09f6c25.

Rule: the grid is a single background color plus several shapes drawn in
color 2. Each shape is an 8-connected component of non-background cells.
Every multi-cell shape is recolored according to its bounding-box aspect
ratio:
  - bounding box wider than tall (w > h)  -> recolor to 1
  - bounding box taller than wide (h > w) -> recolor to 3
  - square bounding box (h == w)          -> recolor to 6
Single isolated cells are noise and erased back to the background color.

infer_T produces a {(r,c): color} mask; apply_T copies the input and
overwrites only the masked cells.
"""

from collections import Counter


def _components(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W:
                        continue
                    if seen[y][x] or grid[y][x] == bg:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy or dx:
                                stack.append((y + dy, x + dx))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter()
    for row in input_grid:
        for v in row:
            cnt[v] += 1
    bg = cnt.most_common(1)[0][0]

    T = {}
    for cells in _components(input_grid, bg):
        if len(cells) == 1:
            (r, c) = cells[0]
            T[(r, c)] = bg
            continue
        minr = min(y for y, x in cells)
        maxr = max(y for y, x in cells)
        minc = min(x for y, x in cells)
        maxc = max(x for y, x in cells)
        bh = maxr - minr + 1
        bw = maxc - minc + 1
        if bw > bh:
            color = 1
        elif bh > bw:
            color = 3
        else:
            color = 6
        for (r, c) in cells:
            T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
