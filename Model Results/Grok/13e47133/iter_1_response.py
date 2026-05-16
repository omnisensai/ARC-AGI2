def solve(input_grid):
    if not input_grid or not input_grid[0]:
        return input_grid
    h = len(input_grid)
    w = len(input_grid[0])
    flat = [cell for row in input_grid for cell in row]
    from collections import Counter
    count = Counter(flat)
    bg = count.most_common(1)[0][0]
    wall = count.most_common(2)[1][0]
    output = [row[:] for row in input_grid]
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
    visited = [[False for _ in range(w)] for _ in range(h)]
    from collections import deque
    for i in range(h):
        for j in range(w):
            if input_grid[i][j] != wall and not visited[i][j]:
                component = []
                q_comp = deque([(i,j)])
                visited[i][j] = True
                while q_comp:
                    r,c = q_comp.popleft()
                    component.append((r,c))
                    for dr,dc in dirs:
                        nr,nc = r+dr, c+dc
                        if 0<=nr<h and 0<=nc<w and input_grid[nr][nc] != wall and not visited[nr][nc]:
                            visited[nr][nc] = True
                            q_comp.append((nr,nc))
                comp_set = set(component)
                border = []
                for r,c in component:
                    is_b = False
                    for dr,dc in dirs:
                        nr = r + dr
                        nc = c + dc
                        if not (0 <= nr < h and 0 <= nc < w) or input_grid[nr][nc] == wall:
                            is_b = True
                            break
                    if is_b:
                        border.append((r,c))
                layer_dict = {}
                vis_layer = set()
                q_layer = deque()
                for pos in border:
                    layer_dict[pos] = 0
                    q_layer.append(pos)
                    vis_layer.add(pos)
                while q_layer:
                    cur = q_layer.popleft()
                    r, c = cur
                    for dr, dc in dirs:
                        nr, nc = r + dr, c + dc
                        pos_n = (nr, nc)
                        if 0<=nr<h and 0<=nc<w and input_grid[nr][nc] != wall and pos_n in comp_set and pos_n not in vis_layer:
                            vis_layer.add(pos_n)
                            layer_dict[pos_n] = layer_dict[cur] + 1
                            q_layer.append(pos_n)
                seed_d = {}
                for r,c in component:
                    colr = input_grid[r][c]
                    if colr != bg:
                        l = layer_dict[(r,c)]
                        seed_d[l] = colr
                maxl = max(seed_d.keys()) if seed_d else 0
                period = maxl + 1
                seq = [bg] * period
                for l, c in seed_d.items():
                    seq[l] = c
                for r,c in component:
                    l = layer_dict[(r,c)]
                    output[r][c] = seq[l % period]
    return output