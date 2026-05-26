"""Canonical solver for ARC task cf133acc.

Structure of every input:
  * Horizontal "bars": a maximal horizontal run of a single color C that has
    one or more single-cell gaps (isolated 0s). Each gap column is an anchor.
  * Vertical "markers": a short vertical run of a single color sitting at an
    anchor column (the cells that are not part of any horizontal bar).

Transformation (latent mask):
  * Fill every gap of every horizontal bar with that bar's color.
  * At each anchor column draw the full vertical line top->bottom, segmented by
    the bar rows: each segment (above / between bars) takes the color of the bar
    at its lower boundary; the region below the lowest bar takes the marker
    color.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    g = input_grid
    bg = 0

    # --- detect horizontal bars ---
    bars = []  # (row, color, cmin, cmax, gaps)
    bar_cells = set()
    for r in range(H):
        colors = {}
        for c in range(W):
            v = g[r][c]
            if v != bg:
                colors.setdefault(v, []).append(c)
        for C, cols in colors.items():
            cmin, cmax = min(cols), max(cols)
            span = cmax - cmin + 1
            if span < 3:
                continue
            missing = [c for c in range(cmin, cmax + 1) if c not in set(cols)]
            isolated = all((m - 1) not in set(missing) for m in missing)
            if 1 <= len(missing) and isolated and len(cols) == span - len(missing):
                bars.append((r, C, cmin, cmax, missing))
                for c in cols:
                    bar_cells.add((r, c))

    # --- group bars by anchor (gap) column ---
    anchor_cols = {}
    for (r, C, cmin, cmax, gaps) in bars:
        for gap in gaps:
            anchor_cols.setdefault(gap, []).append((r, C, cmin, cmax))

    # --- marker color per anchor column (nonzero cell not in any bar) ---
    marker_color = {}
    for col in anchor_cols:
        for r in range(H):
            v = g[r][col]
            if v != bg and (r, col) not in bar_cells:
                marker_color[col] = v
                break

    # --- build latent mask ---
    T = {}

    for (r, C, cmin, cmax, gaps) in bars:
        for gap in gaps:
            T[(r, gap)] = C

    for col, blist in anchor_cols.items():
        prev = 0
        for (br, C, cmin, cmax) in sorted(blist, key=lambda x: x[0]):
            for rr in range(prev, br):
                T[(rr, col)] = C
            T[(br, col)] = C
            prev = br + 1
        mc = marker_color.get(col)
        if mc is not None:
            for rr in range(prev, H):
                T[(rr, col)] = mc

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
