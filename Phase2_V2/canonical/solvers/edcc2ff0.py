"""Canonical solver for ARC puzzle edcc2ff0.

Structure: the grid is split by a solid horizontal divider row whose color is
the most common color in the grid (the "frame"). Below the divider is a frame
field containing small colored components. Above the divider is a legend column
(column 0) holding marker colors.

Rule:
  - For each marker color, count how many components of that color live in the
    frame field. The marker's row becomes a horizontal bar of that color with
    length == that count (anchored at column 0); if the count is 0 the marker
    is erased.
  - Any component in the frame field whose color is NOT a marker color is
    erased (overwritten with the frame color).
"""

from collections import Counter


def _frame_color(grid):
    cnt = Counter(v for row in grid for v in row)
    return cnt.most_common(1)[0][0]


def _divider_row(grid, frame):
    for r, row in enumerate(grid):
        if all(v == frame for v in row):
            return r
    return None


def _components(grid, top, frame):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(top, H):
        for c in range(W):
            v = grid[r][c]
            if v == frame or (r, c) in seen:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                rr, cc = stack.pop()
                if (rr, cc) in seen:
                    continue
                if not (top <= rr < H and 0 <= cc < W):
                    continue
                if grid[rr][cc] != v:
                    continue
                seen.add((rr, cc))
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((rr + dr, cc + dc))
            comps.append((v, cells))
    return comps


def infer_T(input_grid):
    """Return a latent mask {(r,c): new_color} of cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    frame = _frame_color(input_grid)
    div = _divider_row(input_grid, frame)
    if div is None:
        return {}

    # Markers: non-zero cells in column 0 above the divider.
    markers = []  # (row, color)
    for r in range(div):
        v = input_grid[r][0]
        if v != 0:
            markers.append((r, v))
    marker_colors = set(c for _, c in markers)

    # Components in the frame field.
    comps = _components(input_grid, div, frame)
    color_counts = Counter(v for v, _ in comps)

    T = {}

    # Legend bars: each marker row -> bar of length == component count.
    for r, color in markers:
        n = color_counts.get(color, 0)
        for c in range(W):
            T[(r, c)] = color if c < n else 0

    # Erase frame-field components whose color is not a marker color.
    for v, cells in comps:
        if v not in marker_colors:
            for (rr, cc) in cells:
                T[(rr, cc)] = frame

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
