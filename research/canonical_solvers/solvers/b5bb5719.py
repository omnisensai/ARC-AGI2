def infer_T(input_grid):
    """Infer the latent transformation mask.

    Row 0 holds a seed sequence of two interacting colors (2 and 5) over a
    background. Each cell below is generated from its two diagonal parents in
    the row above:
        parents L = (r-1, c-1), R = (r-1, c+1)
          - if L == R: result is the OTHER color of the pair (swap)
          - if L != R: result is R (the right parent)
    The active region narrows by one column on each side per row, forming a
    downward triangle that ends in a point. T maps {(r, c): new_color} for
    every generated (non-background) cell below row 0.
    """
    H, W = len(input_grid), len(input_grid[0])

    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # the two interacting (swappable) colors. They are the non-background
    # colors of this task; both are drawn from {2, 5}. When only one appears
    # in the seed we still know the swap partner is the other of that pair.
    nonbg = sorted({v for v in counts if v != bg})
    if set(nonbg) <= {2, 5}:
        pair_list = [2, 5]
    else:
        pair_list = nonbg
    swap = {}
    if len(pair_list) == 2:
        swap[pair_list[0]] = pair_list[1]
        swap[pair_list[1]] = pair_list[0]

    # build the triangle row by row, starting from row 0 as the known seed
    rows = [list(input_grid[0])]
    for r in range(1, H):
        prev = rows[r - 1]
        cur = [bg] * W
        for c in range(r, W - r):
            L = prev[c - 1] if 0 <= c - 1 < W else bg
            R = prev[c + 1] if 0 <= c + 1 < W else bg
            if L == bg or R == bg:
                continue  # outside the active region
            if L == R:
                cur[c] = swap.get(L, L)
            else:
                cur[c] = R
        rows.append(cur)

    T = {}
    for r in range(1, H):
        for c in range(W):
            if rows[r][c] != bg:
                T[(r, c)] = rows[r][c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
