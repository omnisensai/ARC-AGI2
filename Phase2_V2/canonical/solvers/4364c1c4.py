def _bg(grid):
    cnt = {}
    for row in grid:
        for v in row:
            cnt[v] = cnt.get(v, 0) + 1
    return max(cnt, key=cnt.get)


def _stacks(grid, bg):
    """4-connected components of all non-background cells (each = one stack)."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if not (0 <= a < H and 0 <= b < W) or seen[a][b] or grid[a][b] == bg:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    """Latent mask {(r,c): new_color}.

    Each stack is a vertical run of two color bands. The upper color band is
    shifted one column to the left; the lower color band one column to the
    right. The mask records, for every output cell that differs, its new color
    (or the background where a cell is vacated).
    """
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg(input_grid)
    T = {}
    for cells in _stacks(input_grid, bg):
        # determine the top row of each color in this stack -> ordering
        rows_of = {}
        for r, c in cells:
            col = input_grid[r][c]
            if col not in rows_of or r < rows_of[col]:
                rows_of[col] = r
        # top color = smallest min-row, bottom color = the other
        ordered = sorted(rows_of, key=lambda k: rows_of[k])
        top = ordered[0]
        # shift each cell: top color left (-1), others right (+1)
        moved = {}
        for r, c in cells:
            col = input_grid[r][c]
            dc = -1 if col == top else 1
            nc = c + dc
            if 0 <= nc < W:
                moved[(r, nc)] = col
        # vacate original cells (set to bg) unless filled by a moved cell
        for r, c in cells:
            if (r, c) not in moved:
                T[(r, c)] = bg
        for (r, c), col in moved.items():
            T[(r, c)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
