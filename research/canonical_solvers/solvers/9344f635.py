def find_dominoes(grid, bg):
    """Locate 2-cell objects: vertical -> (col,color), horizontal -> (row,color)."""
    H, W = len(grid), len(grid[0])
    verts, horzs = [], []
    seen = set()
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v == bg or (r, c) in seen:
                continue
            if c + 1 < W and grid[r][c + 1] == v:           # horizontal pair
                horzs.append((r, v)); seen.add((r, c)); seen.add((r, c + 1))
            elif r + 1 < H and grid[r + 1][c] == v:         # vertical pair
                verts.append((c, v)); seen.add((r, c)); seen.add((r + 1, c))
    return verts, horzs


def infer_T(input_grid):
    """Latent mask: vertical dominoes extend into full columns, horizontal
    dominoes extend into full rows. Rows override columns at intersections."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    verts, horzs = find_dominoes(input_grid, bg)
    T = [[None] * W for _ in range(H)]
    for col, color in verts:
        for r in range(H):
            T[r][col] = color
    for row, color in horzs:
        for c in range(W):
            T[row][c] = color
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
