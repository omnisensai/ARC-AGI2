def infer_T(input_grid):
    """Infer the latent transformation mask.

    Markers are cells colored 1. Each marker is the center of a 3x3
    neighborhood; every background (0) cell within that neighborhood becomes
    part of the painted region. Non-background cells in the ring are left
    untouched. Returns a dict {(r, c): new_color}.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    markers = [(r, c) for r in range(H) for c in range(W)
               if input_grid[r][c] == 1]
    T = {}
    for r, c in markers:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W and input_grid[nr][nc] == 0:
                    T[(nr, nc)] = 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
