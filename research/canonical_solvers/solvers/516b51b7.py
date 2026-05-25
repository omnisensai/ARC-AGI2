def infer_T(input_grid):
    """Compute a latent mask {(r,c): new_color}.

    Each maximal 4-connected blob of color 1 is a filled rectangle. We recolor
    it as concentric rings based on each cell's distance to the rectangle border:
    depth 0 (outer ring) stays 1, then the colors alternate 2, 3, 2, 3, ...
    going inward (odd depth -> 2, even depth -> 3).
    """
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False] * W for _ in range(H)]
    T = {}
    for sr in range(H):
        for sc in range(W):
            if input_grid[sr][sc] != 1 or seen[sr][sc]:
                continue
            comp = []
            stack = [(sr, sc)]
            seen[sr][sc] = True
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < H and 0 <= nc < W and not seen[nr][nc]
                            and input_grid[nr][nc] == 1):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            r0 = min(p[0] for p in comp); r1 = max(p[0] for p in comp)
            c0 = min(p[1] for p in comp); c1 = max(p[1] for p in comp)
            for (r, c) in comp:
                depth = min(r - r0, r1 - r, c - c0, c1 - c)
                if depth == 0:
                    color = 1
                elif depth % 2 == 1:
                    color = 2
                else:
                    color = 3
                T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
