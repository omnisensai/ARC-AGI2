"""
Puzzle: 292dd178
Rule name: fill_boxes_and_leak_through_gap

Transformation rule:
For each rectangular box outlined by 1s, fill its interior with 2s and, if the border has a missing 1, extend a line of 2s outward from that gap to the grid edge.

Validation: all 4/4 pairs (training + test) of the source puzzle pass.
Source: Claude agent R1 (v2 full-puzzle prompt — agent saw all pairs including
test answer and wrote code from the full spec).
Judge consensus: 3/5.
"""
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    visited = [[False] * W for _ in range(H)]
    boxes = []
    for i in range(H):
        for j in range(W):
            if input_grid[i][j] == 1 and not visited[i][j]:
                stack = [(i, j)]
                comp = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W or visited[y][x] or input_grid[y][x] != 1:
                        continue
                    visited[y][x] = True
                    comp.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            stack.append((y + dy, x + dx))
                if comp:
                    ys = [c[0] for c in comp]
                    xs = [c[1] for c in comp]
                    boxes.append((min(ys), max(ys), min(xs), max(xs)))

    for (r0, r1, c0, c1) in boxes:
        border_cells = []
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r == r0 or r == r1 or c == c0 or c == c1:
                    border_cells.append((r, c))
        missing = None
        for (r, c) in border_cells:
            if input_grid[r][c] != 1:
                missing = (r, c)
                break
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                grid[r][c] = 2
        if missing is not None:
            mr, mc = missing
            dr = 0
            dc = 0
            if mr == r0:
                dr = -1
            elif mr == r1:
                dr = 1
            if mc == c0:
                dc = -1
            elif mc == c1:
                dc = 1
            r, c = mr, mc
            while 0 <= r < H and 0 <= c < W:
                grid[r][c] = 2
                r += dr
                c += dc

    return grid
