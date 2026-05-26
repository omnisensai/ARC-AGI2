def infer_T(input_grid):
    """Latent mask: 4-connected components of color 3 with size >= 2 -> 8.
    Singleton 3-cells are left unchanged."""
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False] * W for _ in range(H)]
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 3 or seen[r][c]:
                continue
            comp = []
            stack = [(r, c)]
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                comp.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] and input_grid[nr][nc] == 3:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            if len(comp) >= 2:
                for cell in comp:
                    T[cell] = 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
