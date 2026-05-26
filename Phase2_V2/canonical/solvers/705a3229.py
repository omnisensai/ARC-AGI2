def infer_T(input_grid):
    """Each non-background marker shoots two rays of its own color: a vertical
    ray toward the nearer of the top/bottom edge and a horizontal ray toward the
    nearer of the left/right edge (forming an L through the marker)."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    T = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg:
                continue
            # vertical ray toward nearer vertical edge (ties -> top)
            if r <= (H - 1 - r):
                for rr in range(0, r + 1):
                    T[(rr, c)] = v
            else:
                for rr in range(r, H):
                    T[(rr, c)] = v
            # horizontal ray toward nearer horizontal edge (ties -> left)
            if c <= (W - 1 - c):
                for cc in range(0, c + 1):
                    T[(r, cc)] = v
            else:
                for cc in range(c, W):
                    T[(r, cc)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
