"""
Puzzle: 36fdfd69
Rule name: recolor_foreground_in_two_clusters

Transformation rule:
Within the bounding box of each cluster of 2-cells, recolor every foreground (non-zero, non-2) cell to 4.

Validation: all 4/4 pairs (training + test) of the source puzzle pass.
Source: Claude agent R1 (v2 full-puzzle prompt — agent saw all pairs including
test answer and wrote code from the full spec).
Judge consensus: 4/5.
"""
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]
    fg = None
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v != 0 and v != 2:
                fg = v
                break
        if fg is not None:
            break
    twos = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == 2]
    n = len(twos)
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    for i in range(n):
        for j in range(i + 1, n):
            if max(abs(twos[i][0] - twos[j][0]), abs(twos[i][1] - twos[j][1])) <= 2:
                union(i, j)
    clusters = {}
    for i, p in enumerate(twos):
        clusters.setdefault(find(i), []).append(p)
    for cells in clusters.values():
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if grid[r][c] == fg:
                    grid[r][c] = 4
    return grid
