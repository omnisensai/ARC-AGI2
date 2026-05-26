def infer_T(input_grid):
    """Find each rectangle of 5s and mark its strict interior cells to become 2."""
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False]*W for _ in range(H)]
    T = {}
    for sr in range(H):
        for sc in range(W):
            if input_grid[sr][sc] != 5 or seen[sr][sc]:
                continue
            # flood-fill connected component of 5s (4-connectivity)
            comp = []
            stack = [(sr, sc)]
            seen[sr][sc] = True
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] and input_grid[nr][nc] == 5:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            rs = [r for r, c in comp]
            cs = [c for r, c in comp]
            r0, r1 = min(rs), max(rs)
            c0, c1 = min(cs), max(cs)
            # interior = strictly inside the bounding box (keeps a 1-cell border of 5s)
            for r in range(r0 + 1, r1):
                for c in range(c0 + 1, c1):
                    if input_grid[r][c] == 5:
                        T[(r, c)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
