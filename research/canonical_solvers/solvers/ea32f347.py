def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and grid[nr][nc] == color and not seen[nr][nc]:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # the line color = the non-background color present
    fg = None
    for v in counts:
        if v != bg:
            fg = v
            break
    T = [[None] * W for _ in range(H)]
    if fg is None:
        return T
    comps = _components(input_grid, fg)
    # rank components by length (cell count) descending; ties broken stably
    ordered = sorted(range(len(comps)), key=lambda i: len(comps[i]), reverse=True)
    rank_colors = [1, 4, 2]
    for rank, idx in enumerate(ordered):
        if rank < len(rank_colors):
            col = rank_colors[rank]
        else:
            col = fg
        for (r, c) in comps[idx]:
            T[r][c] = col
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
