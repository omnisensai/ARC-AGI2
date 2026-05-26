from collections import defaultdict


def _find_bars(grid):
    """Return list of (col, sorted_rows) for each vertical run of 2s on an edge column."""
    H, W = len(grid), len(grid[0])
    bycol = defaultdict(list)
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 2:
                bycol[c].append(r)
    bars = []
    for c, rows in bycol.items():
        bars.append((c, sorted(rows)))
    return bars


def infer_T(input_grid):
    """Infer the latent overwrite mask {(r,c): color}.

    Structure: two vertical bars of 2 sit on edge columns. Scattered 8 markers
    lie within the row-span of exactly one bar (the "marker bar"); the other
    bar is the "echo bar". For each marker the cells between the bar and the
    marker fill with 8 and the marker cell itself becomes 4 (ray toward the
    bar). The echo bar fills full rows of 8 at the same row-offsets (relative
    to its top) that the markers occupy in the marker bar.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}

    eights = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]
    bars = _find_bars(input_grid)
    if not bars or not eights:
        return T

    # Classify bars: marker bar contains 8 markers within its row span.
    marker_bar = None
    echo_bar = None
    for c, rows in bars:
        lo, hi = rows[0], rows[-1]
        if any(lo <= r <= hi for r, _ in eights):
            marker_bar = (c, rows)
        else:
            echo_bar = (c, rows)

    if marker_bar is None:
        return T

    bcol, brows = marker_bar
    left_side = bcol == 0  # bar on left edge -> rays go leftward toward col 0
    blo = brows[0]

    # Marker bar: each marker shoots a ray of 8 toward the bar; marker -> 4.
    offsets = []
    for (r, c) in eights:
        offsets.append(r - blo)
        if left_side:
            for cc in range(1, c):
                T[(r, cc)] = 8
        else:
            for cc in range(c + 1, W - 1):
                T[(r, cc)] = 8
        T[(r, c)] = 4

    # Echo bar: full rows of 8 at the same offsets (relative to its top).
    if echo_bar is not None:
        ecol, erows = echo_bar
        elo = erows[0]
        for off in offsets:
            r = elo + off
            if 0 <= r < H:
                for cc in range(W):
                    if cc != ecol:
                        T[(r, cc)] = 8

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
