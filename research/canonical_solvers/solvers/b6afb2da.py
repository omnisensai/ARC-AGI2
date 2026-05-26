def infer_T(input_grid):
    """Find rectangular blocks of 5s; mask each block's cells:
    corners -> 1, other border cells -> 4, interior -> 2."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    seen = [[False] * W for _ in range(H)]

    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 5 or seen[r][c]:
                continue
            # flood fill the 4-connected component of 5s
            comp = []
            stack = [(r, c)]
            while stack:
                rr, cc = stack.pop()
                if not (0 <= rr < H and 0 <= cc < W):
                    continue
                if seen[rr][cc] or input_grid[rr][cc] != 5:
                    continue
                seen[rr][cc] = True
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((rr + dr, cc + dc))

            rs = [p[0] for p in comp]
            cs = [p[1] for p in comp]
            rmin, rmax = min(rs), max(rs)
            cmin, cmax = min(cs), max(cs)

            for (rr, cc) in comp:
                on_r = (rr == rmin or rr == rmax)
                on_c = (cc == cmin or cc == cmax)
                if on_r and on_c:
                    T[rr][cc] = 1   # corner
                elif on_r or on_c:
                    T[rr][cc] = 4   # border edge
                else:
                    T[rr][cc] = 2   # interior
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
