"""Canonical solver for ARC task f18ec8cc.

Structure of every input:
  - The grid is partitioned into vertical PANELS: maximal runs of consecutive
    columns sharing one dominant background color.
  - Inside the panels there are a few scattered "marker" cells whose colors are
    the background colors of the OTHER panels.  These markers travel with their
    panel (they are not erased) but they also encode how the panels are
    rearranged.

Transformation: the panels are re-ordered (kept as rigid blocks, widths and
internal contents preserved) so the output has the same dimensions.  Two
re-orderings occur in the corpus:

  * CYCLIC LEFT SHIFT  - the leftmost panel moves to the far right while every
    other panel keeps its relative order.  This is the default.
  * FULL REVERSAL      - the panel order is mirrored.  This happens only when
    the markers form a single clean "ladder": every panel color appears as a
    marker at exactly one consistent row, and those home-rows are strictly
    monotonic with the panels' left-to-right order (i.e. the markers already
    spell out the reversed order).

Both re-orderings send the leftmost panel to the last output position; they
differ only in how the remaining panels are arranged, which the marker ladder
disambiguates.

infer_T computes the source-column permutation and emits a latent mask: a dict
mapping each cell whose color changes to its new color.  apply_T copies the
input and overwrites only the masked cells.
"""

from collections import Counter


def _column_panels(grid):
    """Group columns into panels by per-column dominant (background) color."""
    H = len(grid)
    W = len(grid[0])
    col_bg = []
    for c in range(W):
        cnt = Counter(grid[r][c] for r in range(H))
        col_bg.append(cnt.most_common(1)[0][0])
    panels = []
    start = 0
    for c in range(1, W):
        if col_bg[c] != col_bg[start]:
            panels.append((start, c - 1, col_bg[start]))
            start = c
    panels.append((start, W - 1, col_bg[start]))
    return panels


def _marker_rows(grid, panels):
    """For each panel background color, the set of rows where it appears as a
    marker cell inside any OTHER panel."""
    H = len(grid)
    col_bg = {}
    for (a, b, bg) in panels:
        for c in range(a, b + 1):
            col_bg[c] = bg
    rows = {bg: set() for (_, _, bg) in panels}
    for r in range(H):
        for c in range(len(grid[0])):
            v = grid[r][c]
            if v != col_bg[c] and v in rows:
                rows[v].add(r)
    return rows


def _is_clean_monotonic_ladder(panels, marker_rows):
    """True when every panel color has exactly one marker row and those rows are
    strictly monotonic with the panels' left-to-right order."""
    bgs = [bg for (_, _, bg) in panels]
    if any(len(marker_rows[bg]) != 1 for bg in bgs):
        return False
    hr = [next(iter(marker_rows[bg])) for bg in bgs]
    inc = all(hr[k] < hr[k + 1] for k in range(len(hr) - 1))
    dec = all(hr[k] > hr[k + 1] for k in range(len(hr) - 1))
    return inc or dec


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    panels = _column_panels(input_grid)
    marker_rows = _marker_rows(input_grid, panels)

    n = len(panels)
    if _is_clean_monotonic_ladder(panels, marker_rows):
        order = list(range(n - 1, -1, -1))          # full reversal
    else:
        order = list(range(1, n)) + [0]             # cyclic left shift

    # Build the destination->source column permutation.
    src_cols = []
    for pi in order:
        a, b, _ = panels[pi]
        src_cols.extend(range(a, b + 1))

    # Latent mask: only cells whose value actually changes.
    T = {}
    for r in range(H):
        for dest in range(W):
            src = src_cols[dest]
            new_val = input_grid[r][src]
            if new_val != input_grid[r][dest]:
                T[(r, dest)] = new_val
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
