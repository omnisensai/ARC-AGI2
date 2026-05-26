"""Canonical solver for ARC puzzle fcc82909.

Rule: the grid contains isolated 2x2 blocks of nonzero colors on a 0
background. For each block, count the number of DISTINCT colors it
contains (k). Directly below the block, paint k rows (each 2 cells wide,
aligned to the block's columns) with color 3.

Canonical latent-T form: infer_T builds a mask {(r,c): 3} of the cells to
paint below each block; apply_T overwrites only those cells.
"""

FILL = 3
BG = 0


def _find_blocks(grid):
    """Return list of (top_row, left_col) for each isolated 2x2 nonzero block."""
    H, W = len(grid), len(grid[0])
    blocks = []
    seen = set()
    for r in range(H - 1):
        for c in range(W - 1):
            if (r, c) in seen:
                continue
            cells = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
            if all(grid[a][b] != BG for a, b in cells):
                blocks.append((r, c))
                for a, b in cells:
                    seen.add((a, b))
    return blocks


def infer_T(input_grid):
    """Infer the latent transformation mask: {(r,c): 3} cells below blocks."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for r, c in _find_blocks(input_grid):
        colors = {input_grid[r][c], input_grid[r][c + 1],
                  input_grid[r + 1][c], input_grid[r + 1][c + 1]}
        k = len(colors)
        for i in range(k):
            rr = r + 2 + i
            if 0 <= rr < H:
                if 0 <= c < W:
                    T[(rr, c)] = FILL
                if 0 <= c + 1 < W:
                    T[(rr, c + 1)] = FILL
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
