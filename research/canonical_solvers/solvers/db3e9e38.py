def infer_T(input_grid):
    """Find the vertical 7-line, then emit a diagonal expanding fan of 7/8
    growing upward from the bottom tip. Returns a latent mask {(r,c): color}."""
    H, W = len(input_grid), len(input_grid[0])

    # Locate the vertical segment of 7s: pick the column with the most 7s.
    col_counts = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 7:
                col_counts[c] = col_counts.get(c, 0) + 1
    if not col_counts:
        return {}
    lc = max(col_counts, key=col_counts.get)

    rows7 = [r for r in range(H) if input_grid[r][lc] == 7]
    if not rows7:
        return {}
    r_tip = max(rows7)  # bottom tip of the line

    T = {}
    # For each step d upward from the tip, draw a horizontal span [lc-d, lc+d],
    # coloring cell at horizontal distance k as 7 (k even) or 8 (k odd).
    for d in range(0, r_tip + 1):
        r = r_tip - d
        for c in range(lc - d, lc + d + 1):
            if 0 <= c < W:
                k = abs(c - lc)
                T[(r, c)] = 7 if k % 2 == 0 else 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
