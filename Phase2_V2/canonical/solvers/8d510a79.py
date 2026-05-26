def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # Find the wall: a full row or full column of 5s.
    line_row = None
    for r in range(H):
        if all(input_grid[r][c] == 5 for c in range(W)):
            line_row = r
            break
    line_col = None
    for c in range(W):
        if all(input_grid[r][c] == 5 for r in range(H)):
            line_col = c
            break
    # Latent mask: each colored seed shoots a ray.
    #   color 2 -> ray grows TOWARD the wall (stops just before it)
    #   color 1 -> ray grows AWAY from the wall (out to the grid edge)
    T = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v not in (1, 2):
                continue
            if line_row is not None:
                above = r < line_row
                if v == 2:
                    rng = range(r, line_row) if above else range(line_row + 1, r + 1)
                    for rr in rng:
                        if input_grid[rr][c] == 0 or (rr, c) == (r, c):
                            T[(rr, c)] = 2
                else:
                    rng = range(0, r + 1) if above else range(r, H)
                    for rr in rng:
                        if input_grid[rr][c] == 0 or (rr, c) == (r, c):
                            T[(rr, c)] = 1
            elif line_col is not None:
                left = c < line_col
                if v == 2:
                    rng = range(c, line_col) if left else range(line_col + 1, c + 1)
                    for cc in rng:
                        if input_grid[r][cc] == 0 or (r, cc) == (r, c):
                            T[(r, cc)] = 2
                else:
                    rng = range(0, c + 1) if left else range(c, W)
                    for cc in rng:
                        if input_grid[r][cc] == 0 or (r, cc) == (r, c):
                            T[(r, cc)] = 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
