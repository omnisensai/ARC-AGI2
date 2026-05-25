"""Canonical solver for ARC puzzle 342dd610.

Rule: the grid is a background field (most common color) with isolated colored
pixels. Each colored pixel "drifts" in a fixed direction/distance determined by
its color, leaving the background behind and painting itself at the new cell:
    color 1 -> right 1
    color 2 -> left  2
    color 7 -> up    2
    color 9 -> down  2
infer_T builds the latent mask of cleared source cells and painted destination
cells; apply_T copies the input and overwrites only those masked cells.
"""

# Per-color drift vectors (dr, dc).
COLOR_MOVES = {
    1: (0, 1),    # right 1
    2: (0, -2),   # left 2
    7: (-2, 0),   # up 2
    9: (2, 0),    # down 2
}


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    mask = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg or v not in COLOR_MOVES:
                continue
            dr, dc = COLOR_MOVES[v]
            # Clear the source cell back to background...
            mask[(r, c)] = ('clear', bg)
            nr, nc = r + dr, c + dc
            # ...and paint the pixel at its drifted destination.
            if 0 <= nr < H and 0 <= nc < W:
                mask[(nr, nc)] = ('set', v)
    return mask, bg


def apply_T(input_grid, T):
    mask, bg = T
    out = [row[:] for row in input_grid]
    # Clears first, then sets, so a destination landing on another source wins.
    for (r, c), (op, val) in mask.items():
        if op == 'clear':
            out[r][c] = val
    for (r, c), (op, val) in mask.items():
        if op == 'set':
            out[r][c] = val
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
