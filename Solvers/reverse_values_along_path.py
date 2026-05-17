"""
Puzzle: 5792cb4d
Rule name: reverse_values_along_path

Transformation rule:
Trace the single connected non-background path from one endpoint to the other and write the sequence of cell values back along the path in reverse order.

Validation: all 3/3 pairs (training + test) of the source puzzle pass.
Source: Claude agent R1 (v2 full-puzzle prompt — agent saw all pairs including
test answer and wrote code from the full spec).
Judge consensus: 5/5.
"""
def solve(input_grid):
    from collections import Counter
    H = len(input_grid)
    W = len(input_grid[0])
    cnt = Counter()
    for r in range(H):
        for c in range(W):
            cnt[input_grid[r][c]] += 1
    bg = cnt.most_common(1)[0][0]

    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    cellset = set(cells)

    def neighbors(r, c):
        out = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if (r + dr, c + dc) in cellset:
                out.append((r + dr, c + dc))
        return out

    endpoints = [p for p in cells if len(neighbors(*p)) == 1]
    start = endpoints[0] if endpoints else cells[0]

    path = [start]
    prev = None
    cur = start
    while True:
        nbrs = [n for n in neighbors(*cur) if n != prev]
        if not nbrs:
            break
        prev = cur
        cur = nbrs[0]
        path.append(cur)

    values = [input_grid[r][c] for r, c in path]
    reversed_vals = values[::-1]

    out = [row[:] for row in input_grid]
    for (r, c), v in zip(path, reversed_vals):
        out[r][c] = v
    return out
