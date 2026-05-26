import math
from collections import deque


def _regions(g):
    """Connected components of cells that are not part of the 4/7 frame.

    Returns list of (color, [cells]) for each colored blob."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    regs = []
    for r in range(H):
        for c in range(W):
            if g[r][c] in (4, 7) or seen[r][c]:
                continue
            col = g[r][c]
            q = deque([(r, c)])
            seen[r][c] = True
            cells = []
            while q:
                a, b = q.popleft()
                cells.append((a, b))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    na, nb = a + dr, b + dc
                    if 0 <= na < H and 0 <= nb < W and not seen[na][nb] and g[na][nb] == col:
                        seen[na][nb] = True
                        q.append((na, nb))
            regs.append((col, cells))
    return regs


def infer_T(input_grid):
    """Latent recolor mask.

    The grid has a fixed 4/7 'frame' plus several solid-color blobs arranged
    around the center. Ordering the blobs clockwise by the angle of their
    centroid about the grid center, each blob adopts the color of its
    clockwise-predecessor (colors shift one step clockwise around the ring).
    T maps every blob cell to its new color; frame cells stay None.
    """
    H, W = len(input_grid), len(input_grid[0])
    regs = _regions(input_grid)
    cy = (H - 1) / 2.0
    cx = (W - 1) / 2.0

    ordered = []
    for col, cells in regs:
        sr = sum(a for a, _ in cells) / len(cells)
        sc = sum(b for _, b in cells) / len(cells)
        ang = math.degrees(math.atan2(sc - cx, -(sr - cy))) % 360.0
        ordered.append((ang, col, cells))
    ordered.sort(key=lambda x: x[0])

    n = len(ordered)
    T = {}
    for i in range(n):
        _, _, cells = ordered[i]
        new_col = ordered[(i - 1) % n][1]  # clockwise predecessor's color
        for cell in cells:
            T[cell] = new_col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
