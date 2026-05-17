"""
Puzzle: 1f876c06
Rule name: connect_color_pairs_with_diagonals

Transformation rule:
For each color appearing exactly twice, draw a straight line of that color between its two cells along the axis-aligned or diagonal step direction connecting them.

Validation: all 4/4 pairs (training + test) of the source puzzle pass.
Source: agent-generated R1 code (Claude general-purpose, seed prompt v1).
Judge consensus: initial 5-judge round produced no strict 3+ match;
tiebreaker round (5 new judges picking from 5 prior candidates) produced
5/5 unanimous on this name.
"""
def solve(input_grid):
    h = len(input_grid)
    w = len(input_grid[0])
    out = [[0]*w for _ in range(h)]
    pos = {}
    for r in range(h):
        for c in range(w):
            v = input_grid[r][c]
            if v != 0:
                pos.setdefault(v, []).append((r, c))
    for color, points in pos.items():
        if len(points) == 2:
            (r1, c1), (r2, c2) = points
            dr = r2 - r1
            dc = c2 - c1
            steps = max(abs(dr), abs(dc))
            sr = 0 if dr == 0 else (1 if dr > 0 else -1)
            sc = 0 if dc == 0 else (1 if dc > 0 else -1)
            for i in range(steps + 1):
                out[r1 + i * sr][c1 + i * sc] = color
        else:
            for (r, c) in points:
                out[r][c] = color
    return out
