def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Find each hollow box (4-connected component of non-background cells)
    # and compute its center.
    seen = [[False] * W for _ in range(H)]
    centers = []
    for sr in range(H):
        for sc in range(W):
            if seen[sr][sc] or input_grid[sr][sc] == bg:
                continue
            comp = []
            stack = [(sr, sc)]
            while stack:
                r, c = stack.pop()
                if not (0 <= r < H and 0 <= c < W):
                    continue
                if seen[r][c] or input_grid[r][c] == bg:
                    continue
                seen[r][c] = True
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((r + dr, c + dc))
            rs = [p[0] for p in comp]
            cs = [p[1] for p in comp]
            cr = (min(rs) + max(rs)) // 2
            cc = (min(cs) + max(cs)) // 2
            centers.append((cr, cc))

    # Latent mask: a full-grid cross (color 6) through each box center,
    # painted only over background cells (never over the box border).
    T = [[None] * W for _ in range(H)]
    for (cr, cc) in centers:
        for c in range(W):
            if input_grid[cr][c] == bg:
                T[cr][c] = 6
        for r in range(H):
            if input_grid[r][cc] == bg:
                T[r][cc] = 6
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out
