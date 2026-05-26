def infer_T(input_grid):
    """Infer a latent mask: surround each color-2 marker with a ring of 1s.

    For every cell holding the special marker color (2), each of its 8
    neighboring cells that lies in bounds and currently holds the background
    color (0) is marked to become color 1. Other colored cells are left alone.
    """
    H, W = len(input_grid), len(input_grid[0])
    MARKER = 2
    BG = 0
    RING = 1
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != MARKER:
                continue
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W and input_grid[nr][nc] == BG:
                        T[(nr, nc)] = RING
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
