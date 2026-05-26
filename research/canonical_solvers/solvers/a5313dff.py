def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # flood fill bg cells reachable from the border = exterior background
    exterior = set()
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
        if (r, c) in exterior or not (0 <= r < H and 0 <= c < W):
            continue
        if input_grid[r][c] != bg:
            continue
        exterior.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((r + dr, c + dc))
    # enclosed (non-exterior) background cells get filled with 1
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == bg and (r, c) not in exterior:
                T[r][c] = 1
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
