def infer_T(input_grid):
    """Compute mask of background cells enclosed (not border-reachable) -> color 4."""
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # flood fill bg cells reachable from the border (4-connectivity)
    reachable = set()
    stack = []
    for r in range(H):
        for c in (0, W - 1):
            if input_grid[r][c] == bg:
                stack.append((r, c))
    for c in range(W):
        for r in (0, H - 1):
            if input_grid[r][c] == bg:
                stack.append((r, c))
    while stack:
        r, c = stack.pop()
        if (r, c) in reachable:
            continue
        if not (0 <= r < H and 0 <= c < W):
            continue
        if input_grid[r][c] != bg:
            continue
        reachable.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((r + dr, c + dc))
    # enclosed bg cells = bg cells not reachable from border
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == bg and (r, c) not in reachable:
                T[(r, c)] = 4
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
