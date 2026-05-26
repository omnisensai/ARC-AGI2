def infer_T(input_grid):
    """Latent mask: for each non-background marker, the surrounding 3x3 ring
    cells get a border color determined by the marker's color."""
    H, W = len(input_grid), len(input_grid[0])
    border = {3: 6, 2: 1, 8: 4}
    T = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0 and v in border:
                bc = border[v]
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < H and 0 <= nc < W:
                            T[(nr, nc)] = bc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
