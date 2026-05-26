"""Canonical solver for ARC puzzle d364b489.

Rule: every foreground cell (color 1) is decorated with a fixed cross of
colors in its 4-neighborhood: 7 to the left, 6 to the right, 8 below, 2
above (clipped at grid edges). Decoration never overwrites another
foreground cell.
"""


def infer_T(input_grid):
    """Infer a latent change-mask {(r,c): new_color} from input structure."""
    H, W = len(input_grid), len(input_grid[0])
    fg = 1
    # decoration offsets relative to each foreground cell
    deco = {(0, -1): 7, (0, 1): 6, (1, 0): 8, (-1, 0): 2}
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == fg:
                for (dr, dc), col in deco.items():
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W:
                        if input_grid[nr][nc] != fg:
                            T[(nr, nc)] = col
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
