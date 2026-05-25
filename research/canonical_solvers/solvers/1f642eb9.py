def infer_T(input_grid):
    """Latent mask {(r,c): color}: project each border marker onto the edge
    cell of the 8-block that shares its row (left/right) or column (top/bottom)."""
    H, W = len(input_grid), len(input_grid[0])
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]
    if not cells:
        return {}
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    T = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == 0 or v == 8:
                continue
            if r0 <= r <= r1 and c0 <= c <= c1:
                continue
            # marker on the same row as the block -> nearest vertical edge
            if r0 <= r <= r1:
                if c < c0:
                    T[(r, c0)] = v
                elif c > c1:
                    T[(r, c1)] = v
            # marker on the same column as the block -> nearest horizontal edge
            if c0 <= c <= c1:
                if r < r0:
                    T[(r0, c)] = v
                elif r > r1:
                    T[(r1, c)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
