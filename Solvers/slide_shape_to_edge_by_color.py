"""
Puzzle: f3e62deb
Rule name: slide_shape_to_edge_by_color

Transformation rule:
Move the single hollow square to a grid edge chosen by its color (6=top, 4=bottom, 8=right, 3=left), keeping its perpendicular position unchanged.

Validation: all 8/8 pairs (training + test) of the source puzzle pass.
Source: Claude agent R1 (v2 full-puzzle prompt — agent saw all pairs including
test answer and wrote code from the full spec).
Judge consensus: 3/5.
"""
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    color = 0
    cells = []
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0:
                color = v
                cells.append((r, c))
    out = [[0]*W for _ in range(H)]
    if not cells:
        return out
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    rmin, rmax = min(rs), max(rs)
    cmin, cmax = min(cs), max(cs)
    if color == 6:
        dr, dc = -rmin, 0
    elif color == 4:
        dr, dc = (H - 1 - rmax), 0
    elif color == 8:
        dr, dc = 0, (W - 1 - cmax)
    elif color == 3:
        dr, dc = 0, -cmin
    else:
        dr, dc = 0, 0
    for r, c in cells:
        out[r + dr][c + dc] = color
    return out
