def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # Vertical separator column made entirely of 5s.
    sep = next((c for c in range(W) if all(input_grid[r][c] == 5 for r in range(H))), None)
    # 3x3 template: the colored block in the top-left, left of the separator.
    template = [[input_grid[r][c] for c in range(3)] for r in range(3)]
    # Marker region begins immediately to the right of the separator.
    rc = sep + 1
    # Each 1-marker selects the 3x3 cell of the marker region it lies in.
    marked = set()
    for r in range(H):
        for c in range(rc, W):
            if input_grid[r][c] == 1:
                marked.add((r // 3, (c - rc) // 3))
    # Latent mask: stamp the template into every marked 3x3 cell.
    T = [[None] * W for _ in range(H)]
    for (cr, cc) in marked:
        for i in range(3):
            for j in range(3):
                T[cr * 3 + i][rc + cc * 3 + j] = template[i][j]
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
