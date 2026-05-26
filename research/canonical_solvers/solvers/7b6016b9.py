def infer_T(input_grid):
    """Latent mask: background (0) cells -> 3 if reachable from the outer border
    through other 0-cells, else 2 (enclosed in a sealed room). Line cells stay."""
    H, W = len(input_grid), len(input_grid[0])

    # Flood-fill 0-cells reachable from the grid border (4-connectivity).
    outside = set()
    stack = []
    for r in range(H):
        for c in (0, W - 1):
            if input_grid[r][c] == 0:
                stack.append((r, c))
    for c in range(W):
        for r in (0, H - 1):
            if input_grid[r][c] == 0:
                stack.append((r, c))
    while stack:
        r, c = stack.pop()
        if (r, c) in outside or not (0 <= r < H and 0 <= c < W):
            continue
        if input_grid[r][c] != 0:
            continue
        outside.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((r + dr, c + dc))

    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0:
                T[r][c] = 3 if (r, c) in outside else 2
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
