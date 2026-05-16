def solve(input_grid):
    from collections import Counter
    if not input_grid or not input_grid[0]:
        return []
    rows = len(input_grid)
    cols = len(input_grid[0])
    counter = Counter()
    for r in range(rows):
        for c in range(cols):
            val = input_grid[r][c]
            counter[val] += 1
    if not counter:
        return input_grid
    bg = counter.most_common(1)[0][0]
    wall_c = counter.most_common(2)[1][0] if len(counter) >= 2 else None
    visited = [[False] * cols for _ in range(rows)]
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    def dfs(r, c, component):
        stack = [(r, c)]
        visited[r][c] = True
        while stack:
            cr, cc = stack.pop()
            component.append((cr, cc))
            for dr, dc in directions:
                nr, nc = cr + dr, cc + dc
                if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc] and input_grid[nr][nc] != wall_c:
                    visited[nr][nc] = True
                    stack.append((nr, nc))
    regions = []
    for r in range(rows):
        for c in range(cols):
            if input_grid[r][c] != wall_c and not visited[r][c]:
                component = []
                dfs(r, c, component)
                regions.append(component)
    output = [row[:] for row in input_grid]
    for component in regions:
        if not component:
            continue
        min_r = min(p[0] for p in component)
        max_r = max(p[0] for p in component)
        min_c = min(p[1] for p in component)
        max_c = max(p[1] for p in component)
        layer_to_col = {}
        for pr, pc in component:
            val = input_grid[pr][pc]
            if val != bg:
                lay = min(pr - min_r, max_r - pr, pc - min_c, max_c - pc)
                if lay not in layer_to_col:
                    layer_to_col[lay] = val
        if layer_to_col:
            max_l = max(layer_to_col.keys())
            period = max_l + 1
            color_map = [layer_to_col.get(k, bg) for k in range(period)]
        else:
            period = 1
            color_map = [bg]
        for pr, pc in component:
            lay = min(pr - min_r, max_r - pr, pc - min_c, max_c - pc)
            output[pr][pc] = color_map[lay % period]
    return output