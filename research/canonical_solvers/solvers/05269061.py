def infer_T(input_grid):
    """Latent mask: fill every cell with the color of its anti-diagonal class.

    The grid is a periodic diagonal pattern: all cells on the same anti-diagonal
    (constant r+c) share a color, and the color depends only on (r+c) % 3. The
    non-zero cells reveal which color belongs to each residue class; the rest of
    the grid is reconstructed by periodic tiling.
    """
    H, W = len(input_grid), len(input_grid[0])
    residue_color = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0:
                residue_color[(r + c) % 3] = v
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            res = (r + c) % 3
            if res in residue_color:
                T[r][c] = residue_color[res]
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
