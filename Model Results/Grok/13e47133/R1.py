import collections

def solve(input_grid):
    if not input_grid or not input_grid[0]:
        return input_grid
    h, w = len(input_grid), len(input_grid[0])
    flat = [cell for row in input_grid for cell in row]
    count = collections.Counter(flat)
    bg = count.most_common(1)[0][0]
    wall_color = None
    for c in count:
        if c != bg and all(input_grid[r][c_idx] == c for r in range(h) for c_idx in range(w) if c_idx == 0 or all(input_grid[r][c_idx] == input_grid[r][0] for r in range(h))):
            wall_color = c
            break
    if wall_color is None:
        wall_color = count.most_common(2)[1][0] if len(count) > 1 else bg
    output = [row[:] for row in input_grid]
    visited = [[False] * w for _ in range(h)]
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for i in range(h):
        for j in range(w):
            if not visited[i][j] and input_grid[i][j] != wall_color:
                component = []
                stack = [(i, j)]
                visited[i][j] = True
                while stack:
                    cr, cc = stack.pop()
                    component.append((cr, cc))
                    for dr, dc in dirs:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and input_grid[nr][nc] != wall_color:
                            visited[nr][nc] = True
                            stack.append((nr, nc))
                if component:
                    min_r = min(r for r, c in component)
                    max_r = max(r for r, c in component)
                    min_c = min(c for r, c in component)
                    max_c = max(c for r, c in component)
                    seed_dict = {}
                    for r, c in component:
                        col = input_grid[r][c]
                        if col != bg:
                            layer = min(r - min_r, max_r - r, c - min_c, max_c - c)
                            if layer not in seed_dict:
                                seed_dict[layer] = col
                    if not seed_dict:
                        colors = [bg]
                    else:
                        max_l = max(seed_dict.keys())
                        period = max_l + 1
                        colors = [seed_dict.get(k, bg) for k in range(period)]
                    for r, c in component:
                        layer = min(r - min_r, max_r - r, c - min_c, max_c - c)
                        output[r][c] = colors[layer % len(colors)]
    return output