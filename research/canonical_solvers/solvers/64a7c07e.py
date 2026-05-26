def _components(grid):
    """8-connected components of non-zero cells."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            stack = [(r, c)]
            seen[r][c] = True
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] and grid[nr][nc] != 0:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
            comps.append(cells)
    return comps

def infer_T(input_grid):
    """Each connected component shifts right by its own bounding-box width.
    T = (cells to clear to background, cells to paint with shifted colors)."""
    H, W = len(input_grid), len(input_grid[0])
    clears = set()
    paints = {}
    for cells in _components(input_grid):
        cmin = min(c for _, c in cells)
        cmax = max(c for _, c in cells)
        width = cmax - cmin + 1
        for r, c in cells:
            clears.add((r, c))
        for r, c in cells:
            nc = c + width
            if 0 <= nc < W:
                paints[(r, nc)] = input_grid[r][c]
    return (clears, paints)

def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    clears, paints = T
    for (r, c) in clears:
        out[r][c] = 0
    for (r, c), v in paints.items():
        out[r][c] = v
    return out

def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
