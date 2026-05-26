def infer_T(input_grid):
    """Reflect every off-diagonal non-background cell across the main diagonal
    (transpose). The diagonal carries the marker color (5) and stays fixed.

    Returns a latent mask dict {(r,c): new_color} listing every cell whose
    value changes: each off-diagonal source cell is moved to its transposed
    position, and its original location is cleared to background (when that
    transposed position is itself background).
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    T = {}
    for r in range(H):
        for c in range(W):
            if r == c:
                continue
            v = input_grid[r][c]
            if v == bg:
                continue
            # place this value at its transposed (mirrored) position
            T[(c, r)] = v
            # clear the original position if nothing reflects back into it
            if input_grid[c][r] == bg:
                T[(r, c)] = bg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
