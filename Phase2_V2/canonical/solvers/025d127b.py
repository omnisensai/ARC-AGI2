def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def _components(grid):
    """Connected components (8-connectivity) of identically-colored nonzero cells."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            color = grid[r][c]
            cells = []
            stack = [(r, c)]
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] and grid[nr][nc] == color:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def infer_T(input_grid):
    """
    Latent mask: dict {(r,c): new_color}.
    For each colored shape, keep its bottom row fixed and shift every other row
    one column to the right, clamping each shifted cell's column to the bottom
    row's maximum column. Cells vacated become background (0); new cells take the
    shape's color.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for color, cells in _components(input_grid):
        by_row = {}
        for (r, c) in cells:
            by_row.setdefault(r, []).append(c)
        rows = sorted(by_row)
        bottom = rows[-1]
        bot_max = max(by_row[bottom])
        new_cells = set()
        for r in rows:
            if r == bottom:
                for c in by_row[r]:
                    new_cells.add((r, c))
            else:
                for c in by_row[r]:
                    new_cells.add((r, min(c + 1, bot_max)))
        old_cells = set(cells)
        # paint new positions with color
        for (r, c) in new_cells:
            T[(r, c)] = color
        # clear positions that were part of the shape but no longer occupied
        for (r, c) in old_cells:
            if (r, c) not in new_cells:
                T[(r, c)] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out
