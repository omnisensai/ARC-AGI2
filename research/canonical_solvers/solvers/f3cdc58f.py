def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    colors = [1, 2, 3, 4]
    counts = {c: 0 for c in colors}
    for row in input_grid:
        for v in row:
            if v in counts:
                counts[v] += 1
    # Latent mask: clear the whole grid to 0, then paint bottom-anchored bars.
    T = [[0] * W for _ in range(H)]
    for j, c in enumerate(colors):
        if j >= W:
            break
        h = min(counts[c], H)
        for k in range(h):
            r = H - 1 - k
            T[r][j] = c
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
