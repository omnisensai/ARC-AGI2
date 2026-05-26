def infer_T(input_grid):
    """Compute a latent mask {(r,c): color}.

    Each non-background object is a downward-opening U-box (3 wide). For every
    such object we drop a marker (4) in the bottom row of the grid, in the
    column of the object's center (the gap of the U).
    """
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # connected components of equal-color cells (4-connectivity, per color)
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg and not seen[r][c]:
                color = input_grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    if cr < 0 or cr >= H or cc < 0 or cc >= W:
                        continue
                    if seen[cr][cc] or input_grid[cr][cc] != color:
                        continue
                    seen[cr][cc] = True
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((cr + dr, cc + dc))
                comps.append(cells)

    T = {}
    for cells in comps:
        cols = [cc for _, cc in cells]
        center = (min(cols) + max(cols)) // 2
        T[(H - 1, center)] = 4
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
