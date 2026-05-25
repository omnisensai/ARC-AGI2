def infer_T(input_grid):
    """Find every 3x3 hollow square (ring of eight 1s around a 0 center).
    The mask erases the ring and stamps a plus/cross of color 2 at its center."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for r in range(H - 2):
        for c in range(W - 2):
            ring = [(r, c), (r, c + 1), (r, c + 2),
                    (r + 1, c), (r + 1, c + 2),
                    (r + 2, c), (r + 2, c + 1), (r + 2, c + 2)]
            if all(input_grid[rr][cc] == 1 for rr, cc in ring) and input_grid[r + 1][c + 1] == 0:
                for rr, cc in ring:
                    T[(rr, cc)] = 0
                cr, cc0 = r + 1, c + 1
                for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                    T[(cr + dr, cc0 + dc)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
