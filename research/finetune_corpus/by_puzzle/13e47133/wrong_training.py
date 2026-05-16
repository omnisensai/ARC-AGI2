"""Fine-tuning mirror: 13e47133 / wrong_training.

Auto-generated from wrong_training.jsonl. Each entry below is one
attempt with metadata in the comment header.
"""


# ======================================================================
# Grok R2 -- wrong_training
# training_pass=0/3  training_diff_total=None  test_diff_total=None  test_label=None
# stated_rule: Wall lines divide the grid into 4-connected non-wall regions; each cell's layer is its Chebyshev distance to the nearest perimeter cell (any region cell 8-adjacent to a wall or grid exterior), non-bg seed colors appearing at successive layers within that region form the cycling sequence (bg for any missing layers), and every cell receives the color at (its layer % sequence length) while walls are preserved unchanged.
# source: Model Results/Grok/13e47133/R2.py
# ======================================================================
def solve(input_grid):
    if not input_grid or not input_grid[0]:
        return [row[:] for row in input_grid]
    h, w = len(input_grid), len(input_grid[0])
    flat = [cell for row in input_grid for cell in row]
    count = collections.Counter(flat)
    if not count:
        return [row[:] for row in input_grid]
    bg = count.most_common(1)[0][0]
    wall_color = count.most_common(2)[1][0] if len(count) > 1 else bg
    output = [row[:] for row in input_grid]
    visited = [[False] * w for _ in range(h)]
    dirs4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    dirs8 = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    for i in range(h):
        for j in range(w):
            if not visited[i][j] and input_grid[i][j] != wall_color:
                component = []
                stack = [(i, j)]
                visited[i][j] = True
                while stack:
                    cr, cc = stack.pop()
                    component.append((cr, cc))
                    for dr, dc in dirs4:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and input_grid[nr][nc] != wall_color:
                            visited[nr][nc] = True
                            stack.append((nr, nc))
                if not component:
                    continue
                # perimeter = region cells 8-adjacent to wall or out-of-bounds
                perimeter = set()
                for r, c in component:
                    for dr, dc in dirs8:
                        nr, nc = r + dr, c + dc
                        if not (0 <= nr < h and 0 <= nc < w) or input_grid[nr][nc] == wall_color:
                            perimeter.add((r, c))
                            break
                # BFS (Chebyshev) from perimeter to assign layers inside the component
                layer_dict = {}
                comp_set = set(component)
                if perimeter:
                    queue = deque([(r, c, 0) for r, c in perimeter])
                    vis_dist = set(perimeter)
                    for r, c in perimeter:
                        layer_dict[(r, c)] = 0
                    while queue:
                        cr, cc, dist = queue.popleft()
                        for dr, dc in dirs8:
                            nr, nc = cr + dr, cc + dc
                            if (nr, nc) in comp_set and (nr, nc) not in vis_dist:
                                vis_dist.add((nr, nc))
                                layer_dict[(nr, nc)] = dist + 1
                                queue.append((nr, nc, dist + 1))
                else:
                    for r, c in component:
                        layer_dict[(r, c)] = 0
                # collect seeds per layer within this region only
                seed_dict = {}
                for r, c in component:
                    col = input_grid[r][c]
                    if col != bg:
                        lay = layer_dict.get((r, c), 0)
                        if lay not in seed_dict:
                            seed_dict[lay] = col
                if not seed_dict:
                    colors = [bg]
                else:
                    max_l = max(seed_dict.keys())
                    colors = [seed_dict.get(k, bg) for k in range(max_l + 1)]
                # fill
                for r, c in component:
                    lay = layer_dict.get((r, c), 0)
                    output[r][c] = colors[lay % len(colors)]
    return output

TEST_OUTPUT =
[[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 8, 6, 6, 6, 6, 6, 6, 6, 6, 8, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 8, 6, 4, 4, 4, 4, 4, 4, 6, 8, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 8, 6, 4, 5, 5, 5, 5, 4, 6, 8, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1, 2, 1, 2, 2, 2, 2, 2, 1, 2, 1, 8, 6, 4, 5, 6, 6, 5, 4, 6, 8, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1, 2, 1, 2, 1, 1, 1, 2, 1, 2, 1, 8, 6, 4, 5, 5, 5, 5, 4, 6, 8, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 4, 4, 4, 4, 6, 8, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 4, 6, 6, 6, 6, 8, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 4, 6, 8, 8, 8, 8, 8, 8, 8, 2, 2, 2, 2, 2, 2], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 4, 6, 8, 4, 4, 4, 4, 4, 8, 2, 2, 2, 2, 2, 2], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 4, 6, 8, 4, 1, 1, 1, 4, 8, 2, 2, 2, 2, 2, 2], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 4, 6, 8, 4, 1, 4, 1, 4, 8, 8, 8, 8, 8, 8, 8], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 4, 6, 8, 4, 1, 4, 1, 4, 8, 6, 6, 6, 6, 6, 6], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 4, 6, 8, 4, 1, 1, 1, 4, 8, 6, 4, 4, 4, 4, 6], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 4, 6, 8, 4, 4, 4, 4, 4, 8, 6, 4, 5, 5, 4, 6], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 4, 6, 8, 8, 8, 8, 8, 8, 8, 6, 4, 5, 5, 4, 6], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 4, 6, 6, 6, 6, 6, 6, 6, 6, 6, 4, 5, 5, 4, 6], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 4, 6], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 6], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 4, 6], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 8, 6, 4, 5, 6, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 6, 5, 4, 6], [1, 2, 1, 2, 1, 1, 1, 2, 1, 2, 1, 8, 6, 4, 5, 6, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 6, 5, 4, 6], [1, 2, 1, 2, 2, 2, 2, 2, 1, 2, 1, 8, 6, 4, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 4, 4, 6, 5, 4, 6], [1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 8, 6, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 4, 4, 6, 5, 4, 6], [1, 2, 1, 1, 2, 2, 2, 2, 2, 2, 1, 8, 6, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 6, 4, 4, 6, 5, 4, 6], [1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 8, 6, 6, 6, 6, 6, 6, 6, 6, 6, 4, 5, 6, 4, 4, 6, 5, 4, 6], [1, 2, 1, 1, 2, 1, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 4, 5, 6, 4, 4, 6, 5, 4, 6], [1, 2, 1, 1, 2, 1, 8, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 8, 6, 4, 5, 6, 6, 6, 6, 5, 4, 6], [1, 2, 1, 1, 2, 1, 8, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 8, 6, 4, 5, 5, 5, 5, 5, 5, 4, 6], [1, 2, 2, 2, 2, 1, 8, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 8, 6, 4, 4, 4, 4, 4, 4, 4, 4, 6], [1, 1, 1, 1, 1, 1, 8, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 8, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6]]
