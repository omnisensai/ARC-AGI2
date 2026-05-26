def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # find connected components of same non-zero color (4-connectivity)
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0 and not seen[r][c]:
                color = input_grid[r][c]
                stack = [(r, c)]
                cells = []
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < H and 0 <= nc < W and not seen[nr][nc]
                                and input_grid[nr][nc] == color):
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(cells)

    # For each solid rectangle, blank every other cell of its middle row,
    # starting from the second cell relative to the rectangle's left edge.
    T = {}
    for cells in comps:
        rmin = min(r for r, _ in cells)
        rmax = max(r for r, _ in cells)
        cmin = min(c for _, c in cells)
        cmax = max(c for _, c in cells)
        mid = (rmin + rmax) // 2
        for c in range(cmin, cmax + 1):
            if (c - cmin) % 2 == 1:
                T[(mid, c)] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
