import copy
from collections import Counter, defaultdict, deque
import numpy as np

def solve(input_grid):
    grid = copy.deepcopy(input_grid)
    if not grid or not grid[0]:
        return grid
    h, w = len(grid), len(grid[0])
    grid_np = np.array(grid)

    color_count = Counter()
    for row in grid:
        color_count.update(row)
    sorted_cols = sorted(color_count.items(), key=lambda x: -x[1])
    bg = sorted_cols[0][0]
    wall_color = sorted_cols[1][0]

    walls = grid_np == wall_color
    visited = np.zeros((h, w), dtype=bool)
    regions = defaultdict(list)
    region_seeds = defaultdict(list)
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
    rid = 0

    for r in range(h):
        for c in range(w):
            if not walls[r][c] and not visited[r][c]:
                rid += 1
                queue = [(r, c)]
                visited[r][c] = True
                regions[rid].append((r,c))
                if grid[r][c] not in (bg, wall_color):
                    region_seeds[rid].append(((r,c), grid[r][c]))
                while queue:
                    cr, cc = queue.pop(0)
                    for dr, dc in dirs:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and not walls[nr][nc] and not visited[nr][nc]:
                            visited[nr][nc] = True
                            regions[rid].append((nr, nc))
                            queue.append((nr, nc))
                            if grid[nr][nc] not in (bg, wall_color):
                                region_seeds[rid].append(((nr, nc), grid[nr][nc]))

    for rid in regions:
        region_cells = regions[rid]
        layer = {}
        q = deque()
        vis = set()
        for r,c in region_cells:
            is_bound = False
            for dr,dc in dirs:
                nr, nc = r + dr, c + dc
                if not (0 <= nr < h and 0 <= nc < w) or walls[nr][nc]:
                    is_bound = True
                    break
            if is_bound:
                q.append((r, c))
                vis.add((r, c))
                layer[(r, c)] = 0
        while q:
            cr, cc = q.popleft()
            for dr, dc in dirs:
                nr, nc = cr + dr, cc + dc
                if (nr, nc) in set(region_cells) and (nr, nc) not in vis:
                    vis.add((nr, nc))
                    layer[(nr, nc)] = layer[(cr, cc)] + 1
                    q.append((nr, nc))

        seed_lay = {}
        for (pr, pc), pcol in region_seeds[rid]:
            if (pr, pc) in layer:
                seed_lay[layer[(pr, pc)]] = pcol
        max_ls = max(seed_lay.keys()) if seed_lay else 0
        color_seq = []
        for l in range(max_ls + 1):
            if l in seed_lay:
                color_seq.append(seed_lay[l])
            elif l == 0:
                color_seq.append(bg)
            else:
                color_seq.append(color_seq[0])
        if not color_seq:
            color_seq = [bg]

        for pos in region_cells:
            l = layer[pos]
            colr = color_seq[l % len(color_seq)]
            r, c = pos
            grid[r][c] = colr

    return grid
