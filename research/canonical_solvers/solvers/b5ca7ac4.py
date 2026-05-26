from collections import Counter

def _find_boxes(grid, bg):
    H, W = len(grid), len(grid[0])
    boxes = []
    for r in range(H - 4):
        for c in range(W - 4):
            border = grid[r][c]
            if border == bg:
                continue
            ok = True
            for dc in range(5):
                if grid[r][c + dc] != border or grid[r + 4][c + dc] != border:
                    ok = False
            for dr in range(5):
                if grid[r + dr][c] != border or grid[r + dr][c + 4] != border:
                    ok = False
            if not ok:
                continue
            fill = grid[r + 1][c + 1]
            if fill == border:
                continue
            for dr in range(1, 4):
                for dc in range(1, 4):
                    if grid[r + dr][c + dc] != fill:
                        ok = False
            if not ok:
                continue
            boxes.append([r, c, border, fill])
    return boxes

def _rows_overlap(a, b):
    return not (a[0] + 4 < b[0] or b[0] + 4 < a[0])

def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter()
    for row in input_grid:
        for v in row:
            cnt[v] += 1
    bg = cnt.most_common(1)[0][0]
    boxes = _find_boxes(input_grid, bg)
    # gravity: border 8 slides left, others (border 2) slide right,
    # stacking only against same-border boxes sharing rows.
    moved = [b[:] for b in boxes]
    changed = True
    while changed:
        changed = False
        for i, b in enumerate(moved):
            if b[2] == 8:
                limit = 0
                for j, o in enumerate(moved):
                    if j == i or o[2] != b[2] or not _rows_overlap(b, o):
                        continue
                    if o[1] + 4 < b[1]:
                        limit = max(limit, o[1] + 5)
                if b[1] > limit:
                    b[1] = limit
                    changed = True
            else:
                limit = W - 5
                for j, o in enumerate(moved):
                    if j == i or o[2] != b[2] or not _rows_overlap(b, o):
                        continue
                    if o[1] > b[1] + 4:
                        limit = min(limit, o[1] - 5)
                if b[1] < limit:
                    b[1] = limit
                    changed = True
    # build mask: clear all original box cells to bg, draw boxes at new cols
    T = [[None] * W for _ in range(H)]
    for r, c, border, fill in boxes:
        for dr in range(5):
            for dc in range(5):
                T[r + dr][c + dc] = bg
    for (r, c0, border, fill), m in zip(boxes, moved):
        nc = m[1]
        for dr in range(5):
            for dc in range(5):
                v = border if (dr in (0, 4) or dc in (0, 4)) else fill
                T[r + dr][nc + dc] = v
    return T

def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out

def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
