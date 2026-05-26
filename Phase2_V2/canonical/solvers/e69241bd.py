"""Canonical solver for ARC puzzle e69241bd.

Structure: a grid of 0 (empty) and 5 (wall) cells with a few single-cell
colored markers (any color other than 0/5). Each marker color floods outward
through the orthogonally-connected empty (0) cells; 5-cells act as walls.
When several markers compete for the same empty cell, the marker reached via
the shortest path (multi-source BFS frontier order) claims it. Markers and
walls keep their original color; only empty cells reached by a flood change.
"""

from collections import deque


def _background_and_walls(input_grid):
    """Pick the empty color (most common) and the wall color (next most common)."""
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    ordered = sorted(counts, key=lambda k: counts[k], reverse=True)
    empty = ordered[0]
    wall = ordered[1] if len(ordered) > 1 else None
    return empty, wall


def infer_T(input_grid):
    """Return a latent mask {(r,c): new_color} for empty cells claimed by a flood."""
    H, W = len(input_grid), len(input_grid[0])
    empty, wall = _background_and_walls(input_grid)

    # Markers: any cell that is neither empty nor wall.
    markers = [(r, c, input_grid[r][c])
               for r in range(H) for c in range(W)
               if input_grid[r][c] != empty and input_grid[r][c] != wall]

    owner = [[None] * W for _ in range(H)]
    dq = deque()
    for r, c, col in markers:
        owner[r][c] = col
        dq.append((r, c))

    while dq:
        r, c = dq.popleft()
        col = owner[r][c]
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if (0 <= nr < H and 0 <= nc < W
                    and input_grid[nr][nc] == empty
                    and owner[nr][nc] is None):
                owner[nr][nc] = col
                dq.append((nr, nc))

    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == empty and owner[r][c] is not None:
                T[(r, c)] = owner[r][c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
