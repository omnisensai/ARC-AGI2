"""Canonical solver for ARC puzzle a09f6c25.

Rule: the grid is a single background color plus several shapes drawn in
color 2. Each shape is an 8-connected component of non-background cells.
Every multi-cell shape is recolored according to its mirror symmetry
(computed within its own bounding box):
  - symmetric about its horizontal axis only (top-bottom mirror) -> 1
  - symmetric about its vertical axis only (left-right mirror)   -> 3
  - no axis mirror symmetry (diagonal arrangement)               -> 6
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
        minc = min(x for y, x in cells)
        h = max(y for y, x in cells) - minr + 1
        w = max(x for y, x in cells) - minc + 1
        norm = set((y - minr, x - minc) for y, x in cells)
        lr_sym = all((y, w - 1 - x) in norm for y, x in norm)
        tb_sym = all((h - 1 - y, x) in norm for y, x in norm)
        if tb_sym and not lr_sym:
            color = 1
        elif lr_sym and not tb_sym:
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
