def infer_T(input_grid):
    """Build a latent removal mask {(r,c): 0}.

    A marker box (an L-shaped border of 5s) sits in the top-left corner. Inside
    that box, a single non-zero cell holds a "key" color. The transformation
    deletes every cell in the grid whose color equals the key color, except the
    one(s) inside the protected box interior.
    """
    H, W = len(input_grid), len(input_grid[0])
    fives = set((r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 5)
    if not fives:
        return {}
    # Marker box = connected component of 5s anchored at the top-left corner
    # (ignore any stray 5s elsewhere in the grid).
    start = min(fives, key=lambda rc: (rc[0] + rc[1], rc[0], rc[1]))
    comp = set()
    stack = [start]
    while stack:
        r, c = stack.pop()
        if (r, c) in comp or (r, c) not in fives:
            continue
        comp.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((r + dr, c + dc))
    rmin = min(r for r, c in comp)
    cmin = min(c for r, c in comp)
    rmax = max(r for r, c in comp)
    cmax = max(c for r, c in comp)
    # Interior enclosed by the L-border: rows rmin..rmax-1, cols cmin..cmax-1.
    protected = set()
    key = None
    for r in range(rmin, rmax):
        for c in range(cmin, cmax):
            protected.add((r, c))
            v = input_grid[r][c]
            if v != 0 and v != 5:
                key = v
    if key is None:
        return {}
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == key and (r, c) not in protected:
                T[(r, c)] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
