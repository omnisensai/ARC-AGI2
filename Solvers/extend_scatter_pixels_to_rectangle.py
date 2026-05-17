"""
Puzzle: 2c608aff
Rule name: extend_scatter_pixels_to_rectangle

Transformation rule:
For each scattered pixel that shares a row or column with the solid rectangle, draw a line of that pixel's color from the pixel up to (but not into) the nearest edge of the rectangle.

Validation: all 5/5 pairs (training + test) of the source puzzle pass.
Source: Claude agent R1 (v2 full-puzzle prompt — agent saw all pairs including
test answer and wrote code from the full spec).
Judge consensus: 3/5.
"""
def solve(input_grid):
    from collections import Counter
    H = len(input_grid)
    W = len(input_grid[0])
    cnt = Counter()
    for row in input_grid:
        for v in row:
            cnt[v] += 1
    bg = cnt.most_common(1)[0][0]

    non_bg = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg:
                non_bg.setdefault(v, []).append((r, c))

    rect_color = None
    rect_bounds = None
    for color, cells in non_bg.items():
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        expected = (r1 - r0 + 1) * (c1 - c0 + 1)
        if expected == len(cells) and expected > 1:
            rect_color = color
            rect_bounds = (r0, r1, c0, c1)
            break

    scatter_color = None
    for color in non_bg:
        if color != rect_color:
            scatter_color = color
            break

    out = [row[:] for row in input_grid]
    if rect_color is None or scatter_color is None:
        return out

    r0, r1, c0, c1 = rect_bounds
    for (r, c) in non_bg[scatter_color]:
        if r0 <= r <= r1:
            if c < c0:
                for cc in range(c, c0):
                    out[r][cc] = scatter_color
            elif c > c1:
                for cc in range(c1 + 1, c + 1):
                    out[r][cc] = scatter_color
        elif c0 <= c <= c1:
            if r < r0:
                for rr in range(r, r0):
                    out[rr][c] = scatter_color
            elif r > r1:
                for rr in range(r1 + 1, r + 1):
                    out[rr][c] = scatter_color

    return out
