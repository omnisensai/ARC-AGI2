def _components(grid, bg=0):
    """Connected components (4-connectivity) of background-colored cells."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                cells = []
                while stack:
                    x, y = stack.pop()
                    cells.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < H and 0 <= ny < W and grid[nx][ny] == bg and not seen[nx][ny]:
                            seen[nx][ny] = True
                            stack.append((nx, ny))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    """Lines of color 2 partition the grid into rectangular rooms (regions of 0s).
    The single largest room is painted 1; every smallest room is painted 8;
    all other rooms are left unchanged. T is an explicit {(r,c): color} mask."""
    H, W = len(input_grid), len(input_grid[0])
    comps = _components(input_grid, bg=0)
    T = {}
    if not comps:
        return T
    areas = [len(c) for c in comps]
    mx, mn = max(areas), min(areas)
    for cells in comps:
        a = len(cells)
        if a == mx:
            color = 1
        elif a == mn:
            color = 8
        else:
            color = None
        if color is not None:
            for (r, c) in cells:
                T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
