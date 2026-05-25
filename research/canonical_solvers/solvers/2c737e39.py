def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # 8-connected components of nonzero cells
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    x, y = stack.pop()
                    if x < 0 or x >= H or y < 0 or y >= W:
                        continue
                    if seen[x][y] or input_grid[x][y] == 0:
                        continue
                    seen[x][y] = True
                    cells.append((x, y))
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            if dx or dy:
                                stack.append((x + dx, y + dy))
                comps.append(cells)
    # template = largest component (the multi-cell shape that contains a 5);
    # markers = lone single-cell 5 components elsewhere on the grid.
    template = None
    markers = []
    for cells in comps:
        if len(cells) == 1 and input_grid[cells[0][0]][cells[0][1]] == 5:
            markers.append(cells[0])
        else:
            if template is None or len(cells) > len(template):
                template = cells
    T = {}
    if template is None:
        return T
    # anchor = the 5 inside the template
    anchor = next(((x, y) for (x, y) in template if input_grid[x][y] == 5), None)
    if anchor is None:
        return T
    ar, ac = anchor
    # stamp the template at each marker so its 5 aligns with the marker,
    # but the 5 cell itself is left as background.
    for (mr, mc) in markers:
        dr, dc = mr - ar, mc - ac
        T[(mr, mc)] = 0  # marker 5 cleared (anchor maps here -> background)
        for (x, y) in template:
            if (x, y) == anchor:
                continue
            nx, ny = x + dr, y + dc
            if 0 <= nx < H and 0 <= ny < W:
                T[(nx, ny)] = input_grid[x][y]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
