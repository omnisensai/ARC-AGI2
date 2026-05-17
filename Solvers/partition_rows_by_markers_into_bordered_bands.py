"""
Puzzle: 0f63c0b9
Rule name: partition_rows_by_markers_into_bordered_bands

Transformation rule:
Sort non-zero pixels by row to split the grid into horizontal bands (one per pixel), then paint each band's left/right borders and the pixel's own row in that pixel's color, additionally drawing top/bottom edges for the first and last bands.

Validation: all 5/5 pairs (training + test) of the source puzzle pass.
Source: Claude agent R1 (v2 full-puzzle prompt — agent saw all pairs including
test answer and wrote code from the full spec).
Judge consensus: 4/5 tiebreaker.
"""
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    pixels = []
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0:
                pixels.append((r, c, v))
    pixels.sort()
    n = len(pixels)
    bands = []
    for i, (r, c, v) in enumerate(pixels):
        top = 0 if i == 0 else (pixels[i-1][0] + r) // 2 + 1
        bot = H - 1 if i == n - 1 else (r + pixels[i+1][0]) // 2
        bands.append((top, bot, r, c, v))
    out = [[0]*W for _ in range(H)]
    for i, (top, bot, r, c, v) in enumerate(bands):
        lines = {r}
        if i == 0:
            lines.add(top)
        if i == n - 1:
            lines.add(bot)
        for rr in range(top, bot + 1):
            out[rr][0] = v
            out[rr][W-1] = v
            if rr in lines:
                for cc in range(W):
                    out[rr][cc] = v
    return out
