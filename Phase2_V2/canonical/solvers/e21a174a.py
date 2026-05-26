"""Canonical latent-T solver for ARC puzzle e21a174a.

Rule: the grid contains several objects stacked vertically. Each object is a
single color and occupies a contiguous, non-overlapping band of rows. The
transformation reverses the top-to-bottom stacking order of these bands while
preserving each band's internal row content, re-stacking them contiguously
starting from the original top row of the stack.

infer_T computes, from the input alone, the destination color for every cell of
the restacked region as a mask {(r,c): new_color}; apply_T copies the input and
overwrites only the masked cells.
"""


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    # Collect the rows occupied by each color. Each color forms one contiguous
    # vertical band; bands do not overlap.
    bands = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0:
                bands.setdefault(v, []).append(r)

    if not bands:
        return {}

    band_list = []
    for col, rows in bands.items():
        rs = sorted(set(rows))
        band_list.append((rs[0], rs[-1]))

    # Order bands top-to-bottom by their starting row.
    band_list.sort(key=lambda b: b[0])

    # Re-stack in reversed order beginning at the original top row.
    top = band_list[0][0]

    T = {}
    cursor = top
    for top_r, bot_r in reversed(band_list):
        height = bot_r - top_r + 1
        for k in range(height):
            src_r = top_r + k
            dst_r = cursor + k
            for c in range(W):
                T[(dst_r, c)] = input_grid[src_r][c]
        cursor += height

    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
