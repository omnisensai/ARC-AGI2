"""Canonical solver for ARC puzzle 4612dd53.

Rule: The figure is a lattice of rectangular boxes whose walls are partly
drawn with color 1 (with gaps). Vertical wall columns are the columns that
contain at least one vertical 1-1 adjacency; horizontal wall rows are the rows
that contain at least one horizontal 1-1 adjacency. Each wall line is completed
across the lattice extent (rows span the horizontal-wall rows, cols span the
vertical-wall cols), and every gap (0) lying on a wall line is filled with 2.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    def is1(r, c):
        return 0 <= r < H and 0 <= c < W and input_grid[r][c] == 1

    # Vertical wall columns: columns with a vertical 1-1 adjacency.
    vcols = sorted(set(
        c for r in range(H) for c in range(W) if is1(r, c) and is1(r + 1, c)
    ))
    # Horizontal wall rows: rows with a horizontal 1-1 adjacency.
    hrows = sorted(set(
        r for r in range(H) for c in range(W) if is1(r, c) and is1(r, c + 1)
    ))

    T = {}
    if not vcols or not hrows:
        return T

    rmin, rmax = min(hrows), max(hrows)
    cmin, cmax = min(vcols), max(vcols)

    # Complete each vertical wall over the lattice's row extent.
    for c in vcols:
        for r in range(rmin, rmax + 1):
            if input_grid[r][c] == 0:
                T[(r, c)] = 2
    # Complete each horizontal wall over the lattice's column extent.
    for r in hrows:
        for c in range(cmin, cmax + 1):
            if input_grid[r][c] == 0:
                T[(r, c)] = 2

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
