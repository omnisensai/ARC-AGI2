"""Canonical solver for ARC task fc4aaf52.

Rule (inferred from all train+test pairs):
A single connected shape made of two foreground colors sits on a background.
The shape has a horizontal axis of symmetry; its top half mirrors its bottom
half. The transformation:
  - swaps the two foreground colors (outline <-> fill),
  - keeps the BOTTOM half in its original position,
  - slides the TOP half to the RIGHT so its bottom row begins one column past
    the right edge of the bottom half's top row (a diagonal "explosion").
infer_T builds a latent mask (dict of (r,c)->new_color); apply_T overwrites
only those cells.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    if not cells:
        return {}

    # the two foreground colors -> swap mapping
    fg_colors = sorted({input_grid[r][c] for r, c in cells})
    swap = {}
    if len(fg_colors) == 2:
        a, b = fg_colors
        swap[a], swap[b] = b, a
    else:
        for v in fg_colors:
            swap[v] = v

    rs = [r for r, c in cells]
    r0, r1 = min(rs), max(rs)
    nrows = r1 - r0 + 1
    half = nrows // 2
    top_rows = set(range(r0, r0 + half))
    bot_rows = set(range(r0 + half, r1 + 1))

    # placement of the top half: its bottom row starts one column past the
    # right edge of the bottom half's top row (which stays in place).
    bot_top_row = r0 + half
    top_bot_row = r0 + half - 1
    bot_top_cols = [c for (r, c) in cells if r == bot_top_row]
    top_bot_cols = [c for (r, c) in cells if r == top_bot_row]
    shift = 0
    if bot_top_cols and top_bot_cols:
        shift = max(bot_top_cols) - min(top_bot_cols) + 1

    # latent mask: clear all original foreground cells, then paint the new layout
    T = {}
    for r, c in cells:
        T[(r, c)] = bg
    for r, c in cells:
        if r in bot_rows:
            T[(r, c)] = swap[input_grid[r][c]]
    for r, c in cells:
        if r in top_rows:
            nc = c + shift
            if 0 <= nc < W:
                T[(r, nc)] = swap[input_grid[r][c]]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
