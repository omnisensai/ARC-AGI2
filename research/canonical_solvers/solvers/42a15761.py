"""Canonical solver for ARC puzzle 42a15761.

Structure: the grid is a lattice of 3x3 blocks separated by single 0-rows/cols.
Each block is either "solid" (its center cell == 2) or a "ring" (its center
cell == 0).  Collecting the block centers yields a square matrix of 2/0 values.

Rule: re-order the COLUMNS of that center-matrix by their number of 2s in
descending order (stable: ties keep their original left-to-right order).  This
preserves each row's count of 2s while packing the columns into a staircase.
The latent transformation mask records, for every block-center pixel, its new
value; non-center pixels are never touched.
"""


def _separators(line_is_sep):
    # indices that are full separator lines (all background 0)
    return [i for i, s in enumerate(line_is_sep) if s]


def _block_centers(grid):
    """Return (centers matrix, list of (row,col) pixel coords of each center)."""
    H, W = len(grid), len(grid[0])
    # Separator columns: every cell in the column is 0.
    sep_col = [all(grid[r][c] == 0 for r in range(H)) for c in range(W)]
    sep_row = [all(grid[r][c] == 0 for c in range(W)) for r in range(H)]

    # Build runs of consecutive non-separator columns -> each run is one block col.
    def runs(sep):
        out, start = [], None
        for i, s in enumerate(sep + [True]):
            if s:
                if start is not None:
                    out.append((start, i - 1))
                    start = None
            else:
                if start is None:
                    start = i
        return out

    col_runs = runs(sep_col)
    row_runs = runs(sep_row)
    # center pixel of each block = middle of its run
    col_centers = [(a + b) // 2 for a, b in col_runs]
    row_centers = [(a + b) // 2 for a, b in row_runs]

    centers = [[grid[rc][cc] for cc in col_centers] for rc in row_centers]
    coords = [[(rc, cc) for cc in col_centers] for rc in row_centers]
    return centers, coords


def infer_T(input_grid):
    """Infer the latent transformation mask: {(r,c): new_color} for changed centers."""
    centers, coords = _block_centers(input_grid)
    nbr = len(centers)
    nbc = len(centers[0]) if nbr else 0

    # Column 2-counts; stable descending sort gives the new column order.
    col_count = [sum(1 for r in range(nbr) if centers[r][c] == 2) for c in range(nbc)]
    order = sorted(range(nbc), key=lambda c: -col_count[c])  # stable -> ties keep order

    T = {}
    for r in range(nbr):
        for c in range(nbc):
            new_val = centers[r][order[c]]
            pr, pc = coords[r][c]
            if input_grid[pr][pc] != new_val:
                T[(pr, pc)] = new_val
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
