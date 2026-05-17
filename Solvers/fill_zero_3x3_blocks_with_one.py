"""
Puzzle: 6cf79266
Rule name: fill_zero_3x3_blocks_with_one

Transformation rule:
Find every non-overlapping 3x3 region of all zeros in the grid and recolor those cells to 1.

Validation: all 4/4 pairs (training + test) of the source puzzle pass.
Source: Claude agent R1 (v2 full-puzzle prompt — agent saw all pairs including
test answer and wrote code from the full spec).
Judge consensus: 3/5.
"""
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    used = [[False] * W for _ in range(H)]
    for r in range(H - 2):
        for c in range(W - 2):
            all_zero = True
            for dr in range(3):
                for dc in range(3):
                    if input_grid[r + dr][c + dc] != 0:
                        all_zero = False
                        break
                if not all_zero:
                    break
            if not all_zero:
                continue
            overlap = False
            for dr in range(3):
                for dc in range(3):
                    if used[r + dr][c + dc]:
                        overlap = True
                        break
                if overlap:
                    break
            if overlap:
                continue
            for dr in range(3):
                for dc in range(3):
                    out[r + dr][c + dc] = 1
                    used[r + dr][c + dc] = True
    return out
