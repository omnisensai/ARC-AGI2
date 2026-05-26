"""Canonical latent-T solver for ARC puzzle f5c89df1.

Rule: the grid contains a single template "stamp" made of color 8 surrounding a
center marker (color 3), plus several position markers (color 2). The template's
8-cells are recorded relative to the 3-center. The transformation removes the
original template and all markers, then re-stamps the template (its 8-cells)
centered at each 2-marker location. Cells landing in-bounds become color 8.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Locate the center marker (3), the position markers (2) and the 8-cells.
    center = None
    markers = []
    eights = []
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == 3:
                center = (r, c)
            elif v == 2:
                markers.append((r, c))
            elif v == 8:
                eights.append((r, c))

    # Latent transformation mask: {(r, c): new_color}.
    T = {}
    if center is None:
        return T

    cr, cc = center

    # Template shape: 8-cell offsets relative to the center marker.
    offsets = [(r - cr, c - cc) for (r, c) in eights]

    # Clear the original template footprint (8s, the 3 center, the 2 markers).
    for (r, c) in eights:
        T[(r, c)] = 0
    T[(cr, cc)] = 0
    for (r, c) in markers:
        T[(r, c)] = 0

    # Re-stamp the template centered at each position marker.
    for (mr, mc) in markers:
        for (dr, dc) in offsets:
            nr, nc = mr + dr, mc + dc
            if 0 <= nr < H and 0 <= nc < W:
                T[(nr, nc)] = 8

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
