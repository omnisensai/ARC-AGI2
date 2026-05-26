"""Canonical latent-T solver for ARC puzzle e048c9ed.

Rule (inferred from input structure):
  * The grid contains a single isolated marker cell of color 5 in the top row;
    its COLUMN is the "report column".
  * Every other non-zero object is a horizontal bar (a run of identical cells
    in one row).  Each bar has a length.
  * For each bar a single cell is written at (bar_row, report_column).  Its
    color is decided by the RANK of the bar's length among the distinct bar
    lengths present (shortest length -> rank 0):
        palette = [1, 4, 9, 6]
        - shortest / interior ranks  -> palette[rank]
        - the longest bar            -> palette[3] when there are 4 distinct
                                        lengths, otherwise palette[2]
  * apply_T overwrites only those marker-column cells.
"""

PALETTE = [1, 4, 9, 6]


def _find_bars(grid):
    """Return (marker_col, [(row, length), ...]) found in the input grid."""
    H, W = len(grid), len(grid[0])
    marker_col = None
    bars = []
    for r in range(H):
        c = 0
        while c < W:
            v = grid[r][c]
            if v != 0:
                start = c
                while c < W and grid[r][c] == v:
                    c += 1
                run_len = c - start
                if run_len == 1 and v == 5 and r == 0:
                    # isolated color-5 marker in the top row
                    marker_col = start
                else:
                    bars.append((r, run_len))
            else:
                c += 1
    return marker_col, bars


def infer_T(input_grid):
    """Compute the latent transformation mask: {(r, c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    marker_col, bars = _find_bars(input_grid)
    T = {}
    if marker_col is None or not bars:
        return T

    distinct = sorted({length for _, length in bars})
    n = len(distinct)
    longest = distinct[-1]

    for row, length in bars:
        rank = distinct.index(length)
        if length == longest and n >= 2:
            idx = 3 if n == 4 else 2
        else:
            idx = rank
        if idx >= len(PALETTE):
            idx = len(PALETTE) - 1
        T[(row, marker_col)] = PALETTE[idx]
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
