"""Canonical solver for ARC puzzle 135a2760.

Rule: the grid contains rectangular framed regions. Each region encloses a
periodic pattern (a tile repeated along the region's longer axis) that has been
corrupted in a few cells. For every region, infer the period along the long
axis and snap each cell to the per-phase majority color, repairing the tiling.

infer_T inspects the input alone: it finds the background (most common color),
detects the frame color as the one whose connected components are hollow
rectangle outlines, extracts each region's interior, computes the repaired
periodic content, and records every cell that must change as a latent mask.
apply_T copies the input and overwrites only the masked cells.
"""
from collections import Counter


def _components(g, color):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    out = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == color and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if a < 0 or a >= H or b < 0 or b >= W:
                        continue
                    if seen[a][b] or g[a][b] != color:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                out.append(cells)
    return out


def _frame_score(g, color):
    """Count connected components of `color` that are hollow rectangle outlines."""
    score = 0
    for cells in _components(g, color):
        rs = [a for a, b in cells]
        cs = [b for a, b in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        h, w = r1 - r0 + 1, c1 - c0 + 1
        if h < 3 or w < 3:
            continue
        cellset = set(cells)
        outline_ok = (
            all((r0, c) in cellset and (r1, c) in cellset for c in range(c0, c1 + 1))
            and all((r, c0) in cellset and (r, c1) in cellset for r in range(r0, r1 + 1))
        )
        if outline_ok and len(cells) == 2 * h + 2 * w - 4:
            score += 1
    return score


def _detect_frame(g):
    counts = Counter(v for row in g for v in row)
    bg = counts.most_common(1)[0][0]
    best_color, best_score = None, -1
    for color in counts:
        if color == bg:
            continue
        s = _frame_score(g, color)
        if s > best_score:
            best_color, best_score = color, s
    return best_color


def _repair_region(sub):
    """Snap region interior to its dominant period along the longer axis."""
    H, W = len(sub), len(sub[0])
    axis = 0 if H >= W else 1   # 0 -> rows periodic, 1 -> cols periodic
    L = H if axis == 0 else W
    best = None
    for p in range(1, L // 2 + 1):
        out = [row[:] for row in sub]
        changes = 0
        if axis == 0:
            for ph in range(p):
                for c in range(W):
                    vals = [sub[r][c] for r in range(ph, H, p)]
                    m = Counter(vals).most_common(1)[0][0]
                    for r in range(ph, H, p):
                        if out[r][c] != m:
                            changes += 1
                        out[r][c] = m
        else:
            for ph in range(p):
                for r in range(H):
                    vals = [sub[r][c] for c in range(ph, W, p)]
                    m = Counter(vals).most_common(1)[0][0]
                    for c in range(ph, W, p):
                        if out[r][c] != m:
                            changes += 1
                        out[r][c] = m
        if best is None or (changes, p) < (best[0], best[1]):
            best = (changes, p, out)
    return best[2]


def infer_T(input_grid):
    """Compute latent mask {(r, c): new_color} of cells to repair."""
    H, W = len(input_grid), len(input_grid[0])
    frame = _detect_frame(input_grid)
    T = {}
    if frame is None:
        return T
    for cells in _components(input_grid, frame):
        rs = [a for a, b in cells]
        cs = [b for a, b in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        if r1 - r0 < 2 or c1 - c0 < 2:
            continue
        sub = [[input_grid[r][c] for c in range(c0 + 1, c1)]
               for r in range(r0 + 1, r1)]
        if not sub or not sub[0]:
            continue
        fixed = _repair_region(sub)
        for i in range(len(sub)):
            for j in range(len(sub[0])):
                rr, cc = r0 + 1 + i, c0 + 1 + j
                if fixed[i][j] != input_grid[rr][cc]:
                    T[(rr, cc)] = fixed[i][j]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
