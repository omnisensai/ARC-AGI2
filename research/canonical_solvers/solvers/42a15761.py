"""Canonical solver for ARC puzzle 42a15761.

Structure: the grid is split into vertical strips by full all-0 separator
columns (at columns 3, 7, 11, ...).  Each strip is a 3-column-wide block whose
interior carries a vertical "dot" pattern (some cells are 0 instead of 2).

Rule: reorder the strips left-to-right by their number of 0 ("dot") cells, in
ASCENDING order.  Each strip moves as a whole unit (all rows and its 3 columns);
the sort is stable so strips with equal dot counts keep their original
left-to-right order.

The latent transformation mask `T` records, for every cell, the color that
should occupy it after the strips are reordered.
"""


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    # separator columns = full columns of background 0
    sep = [c for c in range(W) if all(input_grid[r][c] == 0 for r in range(H))]

    # contiguous strip column ranges (start..end inclusive) between separators
    starts = []
    c = 0
    while c < W:
        if c in sep:
            c += 1
            continue
        s = c
        while c < W and c not in sep:
            c += 1
        starts.append((s, c - 1))

    # extract each strip block and its dot (0-cell) count
    strips = []
    for (s, e) in starts:
        block = [[input_grid[r][cc] for cc in range(s, e + 1)] for r in range(H)]
        dots = sum(1 for row in block for v in row if v == 0)
        strips.append((dots, block))

    # stable sort of strip indices by ascending dot count
    order = sorted(range(len(strips)), key=lambda i: strips[i][0])

    # build the latent mask: positional slot 'slot' receives sorted strip 'src'
    T = [[None] * W for _ in range(H)]
    for slot, src in enumerate(order):
        ds, de = starts[slot]
        block = strips[src][1]
        for r in range(H):
            for j, cc in enumerate(range(ds, de + 1)):
                T[r][cc] = block[r][j]
    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
