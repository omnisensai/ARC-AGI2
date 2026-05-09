def solve(input_grid):
    if not input_grid or not input_grid[0]:
        return input_grid
    h = len(input_grid)
    w = len(input_grid[0])
    flat = [cell for row in input_grid for cell in row]
    from collections import Counter
    color_counts = Counter(flat)
    sorted_colors = color_counts.most_common()
    bg_color = sorted_colors[0][0]
    wall_color = sorted_colors[1][0]
    output = [row[:] for row in input_grid]
    visited = [[False] * w for _ in range(h)]
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    from collections import deque
    for i in range(h):
        for j in range(w):
            if output[i][j] == wall_color or visited[i][j]:
                continue
            region_cells = []
            seed_list = []
            q = deque([(i, j)])
            visited[i][j] = True
            region_cells.append((i, j))
            if input_grid[i][j] != bg_color:
                seed_list.append((i, j, input_grid[i][j]))
            while q:
                r, c = q.popleft()
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and input_grid[nr][nc] != wall_color:
                        visited[nr][nc] = True
                        q.append((nr, nc))
                        region_cells.append((nr, nc))
                        if input_grid[nr][nc] != bg_color:
                            seed_list.append((nr, nc, input_grid[nr][nc]))
            if not region_cells:
                continue
            region_set = set(region_cells)
            perimeter = set()
            for r, c in region_cells:
                is_peri = (r == 0 or r == h - 1 or c == 0 or c == w - 1)
                if not is_peri:
                    for dr, dc in dirs:
                        nr, nc = r + dr, c + dc
                        if not (0 <= nr < h and 0 <= nc < w) or input_grid[nr][nc] == wall_color:
                            is_peri = True
                            break
                if is_peri:
                    perimeter.add((r, c))
            depth = {}
            q = deque()
            for pr, pc in perimeter:
                depth[(pr, pc)] = 0
                q.append((pr, pc))
            while q:
                r, c = q.popleft()
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in depth or (nr, nc) not in region_set:
                        continue
                    depth[(nr, nc)] = depth[(r, c)] + 1
                    q.append((nr, nc))
            layer_color = {}
            for sr, sc, scol in seed_list:
                k = depth.get((sr, sc))
                if k is not None:
                    layer_color[k] = scol
            if 0 not in layer_color:
                layer_color[0] = bg_color
            if not layer_color:
                continue
            max_k = max(layer_color.keys())
            period = max_k + 1
            for r, c in region_cells:
                k = depth.get((r, c), 0)
                col_idx = k % period
                output[r][c] = layer_color[col_idx]
    return output