def infer_T(input_grid):
    """Find all marker (8) cells, take their bounding box, and mark the
    rectangle border cells that are currently background as color 1."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    markers = [(r, c) for r in range(H) for c in range(W)
               if input_grid[r][c] != bg]
    T = {}
    if not markers:
        return T
    marker_color = input_grid[markers[0][0]][markers[0][1]]
    r0 = min(r for r, c in markers)
    r1 = max(r for r, c in markers)
    c0 = min(c for r, c in markers)
    c1 = max(c for r, c in markers)
    border = set()
    for c in range(c0, c1 + 1):
        border.add((r0, c))
        border.add((r1, c))
    for r in range(r0, r1 + 1):
        border.add((r, c0))
        border.add((r, c1))
    fill = 1 if marker_color != 1 else 2
    for (r, c) in border:
        if input_grid[r][c] == bg:
            T[(r, c)] = fill
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
