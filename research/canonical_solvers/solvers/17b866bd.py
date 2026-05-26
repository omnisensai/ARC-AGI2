def infer_T(input_grid):
    """Infer the latent transformation mask.

    The grid is a tiling of 5x5 cells whose top-left corners sit on a lattice at
    rows/cols divisible by 5. Each cell has a diamond of 0-cells inside an 8
    border. A lattice intersection holding a non-zero color is a *marker*: it
    "fills" the interior 0-cells of the cell anchored at that intersection with
    the marker's color, and the marker itself is reset to 0.
    """
    H = len(input_grid); W = len(input_grid[0])
    T = {}
    nbr = H // 5; nbc = W // 5
    for i in range(nbr):
        for j in range(nbc):
            r0 = 5 * i; c0 = 5 * j
            m = input_grid[r0][c0]
            if m != 0:
                # reset the marker at this lattice intersection
                T[(r0, c0)] = 0
                # fill the interior 0-cells of this 5x5 cell with the marker color
                for dr in range(1, 5):
                    for dc in range(1, 5):
                        r = r0 + dr; c = c0 + dc
                        if r < H and c < W and input_grid[r][c] == 0:
                            T[(r, c)] = m
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
