"""Canonical solver for ARC puzzle dbc1a6ce.

Rule: The grid holds isolated marker cells (color 1) on a background. Any two
markers that share a row or a column, with no other marker lying strictly
between them, are connected by drawing the connector color (8) on every cell
strictly between the pair. infer_T produces the latent mask of those connector
cells; apply_T overwrites only those cells.
"""

MARKER = 1
CONNECTOR = 8


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    markers = [(r, c) for r in range(H) for c in range(W)
               if input_grid[r][c] == MARKER]
    marker_set = set(markers)

    mask = {}
    for (r1, c1) in markers:
        for (r2, c2) in markers:
            if (r1, c1) >= (r2, c2):
                continue
            if r1 == r2:
                seg = [(r1, c) for c in range(min(c1, c2) + 1, max(c1, c2))]
            elif c1 == c2:
                seg = [(r, c1) for r in range(min(r1, r2) + 1, max(r1, r2))]
            else:
                continue
            if not seg:
                continue
            # only connect nearest aligned markers (no marker strictly between)
            if any((r, c) in marker_set for (r, c) in seg):
                continue
            for (r, c) in seg:
                mask[(r, c)] = CONNECTOR
    return mask


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
