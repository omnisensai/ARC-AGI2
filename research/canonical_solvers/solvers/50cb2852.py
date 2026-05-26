def infer_T(input_grid):
    """Latent mask: for each solid colored rectangle (4-conn component of equal
    nonzero color), mark its interior cells (everything but the 1-cell border)
    to be recolored to 8."""
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False] * W for _ in range(H)]
    T = {}
    for sr in range(H):
        for sc in range(W):
            if seen[sr][sc] or input_grid[sr][sc] == 0:
                continue
            col = input_grid[sr][sc]
            comp = []
            stack = [(sr, sc)]
            seen[sr][sc] = True
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] \
                            and input_grid[nr][nc] == col:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            rs = [r for r, _ in comp]
            cs = [c for _, c in comp]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            cellset = set(comp)
            # interior = strictly inside the component's bounding box
            for r in range(r0 + 1, r1):
                for c in range(c0 + 1, c1):
                    if (r, c) in cellset:
                        T[(r, c)] = 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
