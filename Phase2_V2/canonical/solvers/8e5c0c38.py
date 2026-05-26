"""Canonical solver for ARC puzzle 8e5c0c38.

Rule (same-size grid): the grid contains several monochrome objects on a
background. Each object is "almost" left-right (mirror) symmetric. For every
object we choose the vertical reflection axis that keeps the most cells
(i.e. the closest true symmetry of the shape), then erase every object cell
whose horizontal mirror partner across that axis is empty. Tie-break between
equally-good axes prefers an on-column axis (reflection through a column
center) and then the axis closest to the object centroid.

The transformation mask T marks exactly the object cells to clear (set to
background); apply_T copies the input and clears those cells.
"""

from collections import Counter


def _background(grid):
    counts = Counter(v for row in grid for v in row)
    return counts.most_common(1)[0][0]


def _components(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    nbrs = [(-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)]
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                seen[r][c] = True
                cells = []
                while stack:
                    x, y = stack.pop()
                    cells.append((x, y))
                    for dx, dy in nbrs:
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < H and 0 <= ny < W
                                and not seen[nx][ny] and grid[nx][ny] == color):
                            seen[nx][ny] = True
                            stack.append((nx, ny))
                comps.append((color, cells))
    return comps


def _best_mirror_keep(cells):
    """Cells of the object that survive its best left-right mirror axis."""
    cset = set(cells)
    cols = [c for (_, c) in cells]
    c0, c1 = min(cols), max(cols)
    centroid2 = 2 * sum(cols) / len(cols)

    best = None  # (keep_count, on_column_pref, -centroid_dist, -a2, keep_set)
    # a2 = 2 * axis_position so we cover both on-column (even) and
    # between-column (odd) reflection axes with integer arithmetic.
    for a2 in range(2 * c0, 2 * c1 + 1):
        keep = frozenset((r, c) for (r, c) in cells if (r, a2 - c) in cset)
        key = (len(keep),
               1 if a2 % 2 == 0 else 0,
               -abs(a2 - centroid2),
               -a2)
        if best is None or key > best[0]:
            best = (key, keep)
    return best[1]


def infer_T(input_grid):
    """Latent mask: cells to clear (object cells with no mirror partner)."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    T = [[None] * W for _ in range(H)]
    for color, cells in _components(input_grid, bg):
        keep = _best_mirror_keep(cells)
        for (r, c) in cells:
            if (r, c) not in keep:
                T[r][c] = bg
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
