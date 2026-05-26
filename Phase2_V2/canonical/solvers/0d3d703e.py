def infer_T(input_grid):
    # Fixed color bijection inferred from the corpus (paired swaps):
    # 1<->5, 2<->6, 3<->4, 8<->9. Build a latent mask of recolored cells.
    cmap = {1: 5, 5: 1, 2: 6, 6: 2, 3: 4, 4: 3, 8: 9, 9: 8}
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v in cmap and cmap[v] != v:
                T[r][c] = cmap[v]
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
