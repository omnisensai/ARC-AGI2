def infer_T(input_grid):
    """For each connected component of nonzero cells, fill the background (0)
    cells inside that component's bounding box with 7. Returns a dict mask."""
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False] * W for _ in range(H)]
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0 and not seen[r][c]:
                color = input_grid[r][c]
                comp = []
                stack = [(r, c)]
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if (0 <= nr < H and 0 <= nc < W
                                    and not seen[nr][nc]
                                    and input_grid[nr][nc] == color):
                                seen[nr][nc] = True
                                stack.append((nr, nc))
                rs = [p[0] for p in comp]
                cs = [p[1] for p in comp]
                r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
                for br in range(r0, r1 + 1):
                    for bc in range(c0, c1 + 1):
                        if input_grid[br][bc] == 0:
                            T[(br, bc)] = 7
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
