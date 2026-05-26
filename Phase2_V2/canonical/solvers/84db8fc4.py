def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # Flood-fill 0-cells reachable from the border (4-connectivity).
    reach, stack = set(), []
    for r in range(H):
        for c in range(W):
            if (r in (0, H - 1) or c in (0, W - 1)) and input_grid[r][c] == 0:
                stack.append((r, c))
    while stack:
        r, c = stack.pop()
        if (r, c) in reach:
            continue
        if not (0 <= r < H and 0 <= c < W):
            continue
        if input_grid[r][c] != 0:
            continue
        reach.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((r + dr, c + dc))
    # Latent mask: border-connected 0s -> 2, enclosed 0s -> 5.
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0:
                T[r][c] = 2 if (r, c) in reach else 5
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
