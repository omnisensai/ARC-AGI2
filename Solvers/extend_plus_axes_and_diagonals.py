"""
Puzzle: fe9372f3
Rule name: extend_plus_axes_and_diagonals

Transformation rule:
From the plus-shaped 2-cross, extend its horizontal and vertical axes to the grid edges marking every third cell as 4 and the rest as 8, and draw 1s along both diagonals through the cross center.

Validation: all 3/3 pairs (training + test) of the source puzzle pass.
Source: agent-generated R1 code (Claude general-purpose, seed prompt v1).
Judge consensus: 3/5 LLM judges produced this exact rule name.
"""
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    cr = cc = -1
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 2:
                if (r-1 >= 0 and input_grid[r-1][c] == 2 and
                    r+1 < H and input_grid[r+1][c] == 2 and
                    c-1 >= 0 and input_grid[r][c-1] == 2 and
                    c+1 < W and input_grid[r][c+1] == 2):
                    cr, cc = r, c
    for c in range(W):
        if out[cr][c] != 0:
            continue
        d = abs(c - cc) - 1
        if d <= 0:
            continue
        out[cr][c] = 4 if d % 3 == 0 else 8
    for r in range(H):
        if out[r][cc] != 0:
            continue
        d = abs(r - cr) - 1
        if d <= 0:
            continue
        out[r][cc] = 4 if d % 3 == 0 else 8
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        r, c = cr + dr, cc + dc
        while 0 <= r < H and 0 <= c < W:
            if out[r][c] == 0:
                out[r][c] = 1
            r += dr
            c += dc
    return out
