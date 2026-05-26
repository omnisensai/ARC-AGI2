"""Canonical ARC solver for puzzle bf89d739.

Rule (inferred from input structure):
  - The grid contains scattered marker cells of color 2 on a background of 0.
  - Exactly one "trunk" line exists: either a row that contains exactly two
    markers, or a column that contains exactly two markers. The trunk runs
    along that line between its two markers.
  - Every other marker is a "branch": it connects perpendicularly to the trunk.
    If the trunk is a row R, a branch marker at (r,c) draws a vertical segment
    in column c spanning between row r and row R (joining the trunk at (R,c)).
    If the trunk is a column C, a branch marker at (r,c) draws a horizontal
    segment in row r spanning between column c and column C.
  - All drawn connector cells (trunk interior + branch interior + the trunk
    junction cell of each branch) become color 3. Original markers stay 2.

infer_T computes the latent mask of cells to paint 3; apply_T overwrites only
those cells.
"""

MARKER = 2
FILL = 3


def _markers(grid):
    H, W = len(grid), len(grid[0])
    return [(r, c) for r in range(H) for c in range(W) if grid[r][c] == MARKER]


def infer_T(input_grid):
    """Return a dict {(r,c): new_color} latent transformation mask."""
    H, W = len(input_grid), len(input_grid[0])
    markers = _markers(input_grid)

    # Group markers by row and by column to find the trunk line.
    by_row = {}
    by_col = {}
    for (r, c) in markers:
        by_row.setdefault(r, []).append(c)
        by_col.setdefault(c, []).append(r)

    trunk_rows = [r for r, cs in by_row.items() if len(cs) == 2]
    trunk_cols = [c for c, rs in by_col.items() if len(rs) == 2]

    T = {}
    if not trunk_rows and not trunk_cols:
        return T  # no recognizable trunk; nothing to draw

    if trunk_rows:
        # Horizontal trunk on row R.
        R = trunk_rows[0]
        c0, c1 = sorted(by_row[R])
        # Trunk interior cells.
        for c in range(c0 + 1, c1):
            if input_grid[R][c] != MARKER:
                T[(R, c)] = FILL
        # Branches: every marker not part of the trunk pair.
        for (r, c) in markers:
            if r == R and c in (c0, c1):
                continue
            lo, hi = (r, R) if r < R else (R, r)
            for rr in range(lo, hi + 1):
                if (rr, c) == (r, c):
                    continue  # keep the branch marker itself
                if input_grid[rr][c] != MARKER:
                    T[(rr, c)] = FILL
    else:
        # Vertical trunk on column C.
        C = trunk_cols[0]
        r0, r1 = sorted(by_col[C])
        for r in range(r0 + 1, r1):
            if input_grid[r][C] != MARKER:
                T[(r, C)] = FILL
        for (r, c) in markers:
            if c == C and r in (r0, r1):
                continue
            lo, hi = (c, C) if c < C else (C, c)
            for cc in range(lo, hi + 1):
                if (r, cc) == (r, c):
                    continue
                if input_grid[r][cc] != MARKER:
                    T[(r, cc)] = FILL

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
