"""
Puzzle: d6ad076f
Rule name: fill_inner_gap_between_rectangles

Transformation rule:
Between the two non-zero rectangles, fill the rectangular region bounded by their overlapping rows/columns (shrunk by one on each side) with color 8.

Validation: all 4/4 pairs (training + test) of the source puzzle pass.
Source: Claude agent R1 (v2 full-puzzle prompt — agent saw all pairs including
test answer and wrote code from the full spec).
Judge consensus: 5/5 tiebreaker.
"""
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]
    seen_colors = set()
    rects = []
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v != 0 and v not in seen_colors:
                seen_colors.add(v)
                cells = [(rr, cc) for rr in range(H) for cc in range(W) if grid[rr][cc] == v]
                r0 = min(p[0] for p in cells)
                r1 = max(p[0] for p in cells)
                c0 = min(p[1] for p in cells)
                c1 = max(p[1] for p in cells)
                rects.append((r0, r1, c0, c1, v))
    if len(rects) != 2:
        return grid
    a, b = rects
    ar0, ar1, ac0, ac1, _ = a
    br0, br1, bc0, bc1, _ = b
    if ac1 < bc0 or bc1 < ac0:
        if ac1 < bc0:
            gap_c0, gap_c1 = ac1 + 1, bc0 - 1
        else:
            gap_c0, gap_c1 = bc1 + 1, ac0 - 1
        r0 = max(ar0, br0) + 1
        r1 = min(ar1, br1) - 1
        for r in range(r0, r1 + 1):
            for c in range(gap_c0, gap_c1 + 1):
                grid[r][c] = 8
    else:
        if ar1 < br0:
            gap_r0, gap_r1 = ar1 + 1, br0 - 1
        else:
            gap_r0, gap_r1 = br1 + 1, ar0 - 1
        c0 = max(ac0, bc0) + 1
        c1 = min(ac1, bc1) - 1
        for r in range(gap_r0, gap_r1 + 1):
            for c in range(c0, c1 + 1):
                grid[r][c] = 8
    return grid
