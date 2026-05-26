def infer_T(input_grid):
    """Each 5 marker is the center of a 3x3 stamp: corners stay 5,
    edge-midpoints become 1, and the center cell is cleared to 0.
    Returns a latent mask {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    markers = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 5]
    T = {}
    for (r, c) in markers:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < H and 0 <= cc < W):
                    continue
                if dr == 0 and dc == 0:
                    color = 0          # center cell cleared
                elif dr != 0 and dc != 0:
                    color = 5          # diagonal corner
                else:
                    color = 1          # orthogonal edge midpoint
                T[(rr, cc)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
