def infer_T(input_grid):
    """Infer the latent transformation mask.

    Row 0 holds a seed sequence of two non-background colors. Each cell below
    is generated from its two diagonal parents in the row above:
      parents L = (r-1, c-1), R = (r-1, c+1)
        - if L == R: result is the OTHER of the two seed colors (swap)
        - if L != R: result is R (the right parent)
    The pyramid narrows by one column on each side per row, ending in a point.
    T maps {(r, c): new_color} for every generated (non-background) cell.
    """
    H, W = len(input_grid), len(input_grid[0])

    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # the two seed colors come from row 0
    seed_colors = sorted({v for v in input_grid[0] if v != bg})

    # build the pyramid row by row, starting from row 0 as the known seed
    rows = [list(input_grid[0])]
    for r in range(1, H):
        prev = rows[r - 1]
        cur = [bg] * W
        for c in range(r, W - r):
            L = prev[c - 1] if 0 <= c - 1 < W else bg
            R = prev[c + 1] if 0 <= c + 1 < W else bg
            if L == bg or R == bg:
                # outside the active region; skip
                continue
            if L == R:
                # swap to the other seed color
                if len(seed_colors) == 2:
                    cur[c] = seed_colors[0] if L == seed_colors[1] else seed_colors[1]
                else:
                    cur[c] = L
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
