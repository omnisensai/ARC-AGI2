"""
Puzzle: 95990924
Rule name: mark_2x2_block_diagonal_corners

Transformation rule:
For each 2x2 block of 5s, place 1, 2, 3, 4 at the four diagonally adjacent cells just outside its top-left, top-right, bottom-left, and bottom-right corners.

Validation: all 4/4 pairs (training + test) of the source puzzle pass.
Source: agent-generated R1 code (Claude general-purpose, seed prompt v1).
Judge consensus: 5/5 LLM judges produced this exact rule name.
"""
def solve(input_grid):
    h = len(input_grid)
    w = len(input_grid[0])
    out = [row[:] for row in input_grid]
    seen = set()
    for r in range(h - 1):
        for c in range(w - 1):
            if (r, c) in seen:
                continue
            if (input_grid[r][c] == 5 and input_grid[r][c+1] == 5
                    and input_grid[r+1][c] == 5 and input_grid[r+1][c+1] == 5):
                seen.add((r, c))
                for (rr, cc, v) in [(r-1, c-1, 1), (r-1, c+2, 2), (r+2, c-1, 3), (r+2, c+2, 4)]:
                    if 0 <= rr < h and 0 <= cc < w and out[rr][cc] == 0:
                        out[rr][cc] = v
    return out
