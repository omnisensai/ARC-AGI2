def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _path_cells(grid):
    """Return the colored cells as a list, ordered from one endpoint to the
    other along the single 4-connected simple chain they form."""
    H, W = len(grid), len(grid[0])
    bg = _background(grid)
    cells = set((r, c) for r in range(H) for c in range(W) if grid[r][c] != bg)
    if not cells:
        return []

    def neighbors(r, c):
        return [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if (r + dr, c + dc) in cells]

    # endpoints = cells with exactly one neighbor along the chain
    endpoints = [p for p in cells if len(neighbors(*p)) == 1]
    if len(endpoints) >= 1:
        start = min(endpoints)
    else:
        start = min(cells)  # closed loop fallback: pick a deterministic start

    path = [start]
    seen = {start}
    while True:
        r, c = path[-1]
        nxt = [p for p in neighbors(r, c) if p not in seen]
        if not nxt:
            break
        path.append(nxt[0])
        seen.add(nxt[0])
    return path


def infer_T(input_grid):
    """Latent mask: map each path cell to the color found at the mirrored
    position along the chain (reverse the color sequence along the path)."""
    path = _path_cells(input_grid)
    colors = [input_grid[r][c] for (r, c) in path]
    reversed_colors = colors[::-1]
    T = {}
    for i, (r, c) in enumerate(path):
        new_color = reversed_colors[i]
        if new_color != input_grid[r][c]:
            T[(r, c)] = new_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
