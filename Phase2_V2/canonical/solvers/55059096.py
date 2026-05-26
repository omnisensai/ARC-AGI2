def infer_T(input_grid):
    """Infer a latent mask {(r,c): color} of diagonal connector cells.

    Structure: the grid contains plus-shaped crosses of color 3 (a center
    cell whose four orthogonal neighbors are also 3). For every pair of cross
    centers that lie on a perfect diagonal (|dr| == |dc|), a diagonal line of
    color 2 is drawn between them, skipping any cell occupied by a cross.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Locate cross centers: a 3 with all four orthogonal neighbors == 3.
    centers = []
    for r in range(H):
        for c in range(W):
            if (input_grid[r][c] == 3 and 0 < r < H - 1 and 0 < c < W - 1
                    and input_grid[r - 1][c] == 3 and input_grid[r + 1][c] == 3
                    and input_grid[r][c - 1] == 3 and input_grid[r][c + 1] == 3):
                centers.append((r, c))

    # Cells occupied by any cross (center plus its four arms).
    cross_cells = set()
    for (r, c) in centers:
        for dr, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            cross_cells.add((r + dr, c + dc))

    T = {}
    n = len(centers)
    for i in range(n):
        for j in range(i + 1, n):
            r1, c1 = centers[i]
            r2, c2 = centers[j]
            dr, dc = r2 - r1, c2 - c1
            if dr != 0 and abs(dr) == abs(dc):
                sr = 1 if dr > 0 else -1
                sc = 1 if dc > 0 else -1
                for k in range(1, abs(dr)):
                    rr, cc = r1 + sr * k, c1 + sc * k
                    if (rr, cc) not in cross_cells:
                        T[(rr, cc)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
