"""Fine-tuning mirror: 13e47133 / wrong_training.

Auto-generated from wrong_training.jsonl. Each entry below is one
attempt with metadata in the comment header.
"""


# ======================================================================
# GPT iter 1 -- wrong_training
# training_pass=2/3  training_diff_total=26  test_diff_total=255  test_label=FALSE_CONFIDENT_SUBMIT
# stated_rule: (none)
# source: Model Results/GPT/13e47133/iter_1_response.py
# ======================================================================
def solve(input_grid):
    from collections import Counter, deque

    grid = input_grid
    h, w = len(grid), len(grid[0])

    counts = Counter(v for row in grid for v in row)
    background = counts.most_common(1)[0][0]

    # The barrier is the most common non-background color.
    barrier = max((c for c in counts if c != background), key=lambda c: counts[c])

    output_grid = [row[:] for row in grid]
    seen = [[False] * w for _ in range(h)]
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for sr in range(h):
        for sc in range(w):
            if seen[sr][sc] or grid[sr][sc] == barrier:
                continue

            # 4-connected component of non-barrier cells.
            q = deque([(sr, sc)])
            seen[sr][sc] = True
            cells = []

            while q:
                r, c = q.popleft()
                cells.append((r, c))

                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] != barrier
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))

            min_r = min(r for r, c in cells)
            max_r = max(r for r, c in cells)
            min_c = min(c for r, c in cells)
            max_c = max(c for r, c in cells)

            # Seeds are non-background, non-barrier cells inside this component.
            colors_by_depth = {}
            for r, c in cells:
                if grid[r][c] != background:
                    depth = min(r - min_r, max_r - r, c - min_c, max_c - c)
                    colors_by_depth.setdefault(depth, grid[r][c])

            if not colors_by_depth:
                continue

            max_depth_seed = max(colors_by_depth)
            cycle = [background] * (max_depth_seed + 1)

            for depth, color in colors_by_depth.items():
                cycle[depth] = color

            period = len(cycle)

            for r, c in cells:
                depth = min(r - min_r, max_r - r, c - min_c, max_c - c)
                output_grid[r][c] = cycle[depth % period]

    return output_grid


# ======================================================================
# GPT iter 2 -- wrong_training
# training_pass=2/3  training_diff_total=4  test_diff_total=152  test_label=FALSE_CONFIDENT_SUBMIT
# stated_rule: (none)
# source: Model Results/GPT/13e47133/iter_2_response.py
# ======================================================================
def solve(input_grid):
    from collections import Counter, deque, defaultdict

    grid = input_grid
    h, w = len(grid), len(grid[0])

    counts = Counter(v for row in grid for v in row)
    background = counts.most_common(1)[0][0]

    non_bg = [c for c in counts if c != background]
    barrier = max(non_bg, key=lambda c: counts[c])

    out = [row[:] for row in grid]
    seen = [[False] * w for _ in range(h)]
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for sr in range(h):
        for sc in range(w):
            if seen[sr][sc] or grid[sr][sc] == barrier:
                continue

            q = deque([(sr, sc)])
            seen[sr][sc] = True
            comp = []

            while q:
                r, c = q.popleft()
                comp.append((r, c))
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] != barrier
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))

            comp_set = set(comp)

            # Split each connected free-space component into maximal rectangles
            # made from equal horizontal runs. This fixes C-shaped components
            # around internal wall segments.
            runs_by_span = defaultdict(list)

            rows = sorted(set(r for r, c in comp))
            for r in rows:
                c = 0
                while c < w:
                    while c < w and (r, c) not in comp_set:
                        c += 1
                    if c >= w:
                        break
                    l = c
                    while c < w and (r, c) in comp_set:
                        c += 1
                    rr = c - 1
                    runs_by_span[(l, rr)].append(r)

            rects = []
            for (l, rr), rs in runs_by_span.items():
                rs.sort()
                start = prev = rs[0]
                for r in rs[1:]:
                    if r == prev + 1:
                        prev = r
                    else:
                        rects.append((start, prev, l, rr))
                        start = prev = r
                rects.append((start, prev, l, rr))

            rect_cycles = {}
            component_cycles = []

            for idx, (r0, r1, c0, c1) in enumerate(rects):
                colors_by_depth = {}

                for r in range(r0, r1 + 1):
                    for c in range(c0, c1 + 1):
                        val = grid[r][c]
                        if val != background and val != barrier:
                            d = min(r - r0, r1 - r, c - c0, c1 - c)
                            colors_by_depth.setdefault(d, val)

                if colors_by_depth:
                    max_d = max(colors_by_depth)
                    cycle = [background] * (max_d + 1)
                    for d, val in colors_by_depth.items():
                        cycle[d] = val
                    rect_cycles[idx] = cycle
                    component_cycles.append(cycle)

            if not component_cycles:
                continue

            inherited = component_cycles[0]

            for idx, (r0, r1, c0, c1) in enumerate(rects):
                cycle = rect_cycles.get(idx, inherited)
                period = len(cycle)

                for r in range(r0, r1 + 1):
                    for c in range(c0, c1 + 1):
                        d = min(r - r0, r1 - r, c - c0, c1 - c)
                        out[r][c] = cycle[d % period]

    return out


# ======================================================================
# Gemini iter 1 -- wrong_training
# training_pass=0/3  training_diff_total=None  test_diff_total=None  test_label=None
# stated_rule: (none)
# source: Model Results/Gemini/13e47133/iter_1_response.py
# ======================================================================
import numpy as np

def solve(input_grid):
    grid = np.array(input_grid)
    rows, cols = grid.shape
    output = grid.copy()

    # 1. Identify Divider Lines
    # Dividers are rows/cols that are mostly the same color (not the background)
    def find_dividers(arr):
        divs = []
        for i, line in enumerate(arr):
            unique, counts = np.unique(line, return_counts=True)
            if len(unique) > 1:
                # If a line has a dominant color that isn't the background (found via mode)
                mode_color = unique[np.argmax(counts)]
                if counts[np.argmax(counts)] > len(line) * 0.5:
                    # Check if this color is consistent across the grid as a divider
                    divs.append((i, mode_color))
        return divs

    row_divs = []
    # Identify horizontal dividers
    for r in range(rows):
        unique, counts = np.unique(grid[r, :], return_counts=True)
        if len(unique) <= 3 and counts.max() > cols * 0.6:
            row_divs.append(r)
            
    col_divs = []
    # Identify vertical dividers
    for c in range(cols):
        unique, counts = np.unique(grid[:, c], return_counts=True)
        if len(unique) <= 3 and counts.max() > rows * 0.6:
            col_divs.append(c)

    # 2. Define Regions
    r_bounds = [0] + row_divs + [rows]
    c_bounds = [0] + col_divs + [cols]

    for i in range(len(r_bounds)-1):
        for j in range(len(c_bounds)-1):
            r1, r2 = r_bounds[i], r_bounds[i+1]
            c1, c2 = c_bounds[j], c_bounds[j+1]
            
            # Adjust to exclude divider lines
            sub_r1 = r1 + (1 if i > 0 else 0)
            sub_r2 = r2 - (1 if i < len(r_bounds)-2 else 0)
            sub_c1 = c1 + (1 if j > 0 else 0)
            sub_c2 = c2 - (1 if j < len(c_bounds)-2 else 0)
            
            # Find seeds in this region
            region = grid[r1:r2, c1:c2]
            bg_color = np.bincount(region.flatten()).argmax()
            seeds = []
            for rr in range(r1, r2):
                for cc in range(c1, c2):
                    if grid[rr, cc] != bg_color and (rr not in row_divs) and (cc not in col_divs):
                        seeds.append(((rr, cc), grid[rr, cc]))
            
            if not seeds:
                # Fill with background or corner color if logic dictates
                output[r1:r2, c1:c2] = grid[r1, c1]
                continue

            # Expansion Logic: Concentric rings
            # Determine rings based on distance from region boundary
            h = r2 - r1
            w = c2 - c1
            num_rings = (min(h, w) + 1) // 2
            
            # Map seeds to rings
            ring_colors = {}
            for (sr, sc), sc_val in seeds:
                dist = min(sr - r1, r2 - 1 - sr, sc - c1, c2 - 1 - sc)
                ring_colors[dist] = sc_val
            
            # Determine outer color (corner seed or existing)
            outer_color = grid[r1, c1]
            
            current_color = outer_color
            for dist in range(num_rings):
                if dist in ring_colors:
                    current_color = ring_colors[dist]
                
                # Fill the ring
                for rr in range(r1 + dist, r2 - dist):
                    for cc in range(c1 + dist, c2 - dist):
                        # Only fill the "border" of the current inner rectangle
                        if rr == r1 + dist or rr == r2 - 1 - dist or \
                           cc == c1 + dist or cc == c2 - 1 - dist:
                            output[rr, cc] = current_color

    return output.tolist()


# ======================================================================
# Gemini iter 2 -- wrong_training
# training_pass=0/3  training_diff_total=None  test_diff_total=None  test_label=None
# stated_rule: (none)
# source: Model Results/Gemini/13e47133/iter_2_response.py
# ======================================================================
import numpy as np

def solve(input_grid):
    grid = np.array(input_grid)
    rows, cols = grid.shape
    output = grid.copy()

    # 1. Identify Divider Lines
    # Dividers are rows/cols that are mostly the same color (not the background)
    def find_dividers(arr):
        divs = []
        for i, line in enumerate(arr):
            unique, counts = np.unique(line, return_counts=True)
            if len(unique) > 1:
                # If a line has a dominant color that isn't the background (found via mode)
                mode_color = unique[np.argmax(counts)]
                if counts[np.argmax(counts)] > len(line) * 0.5:
                    # Check if this color is consistent across the grid as a divider
                    divs.append((i, mode_color))
        return divs

    row_divs = []
    # Identify horizontal dividers
    for r in range(rows):
        unique, counts = np.unique(grid[r, :], return_counts=True)
        if len(unique) <= 3 and counts.max() > cols * 0.6:
            row_divs.append(r)
            
    col_divs = []
    # Identify vertical dividers
    for c in range(cols):
        unique, counts = np.unique(grid[:, c], return_counts=True)
        if len(unique) <= 3 and counts.max() > rows * 0.6:
            col_divs.append(c)

    # 2. Define Regions
    r_bounds = [0] + row_divs + [rows]
    c_bounds = [0] + col_divs + [cols]

    for i in range(len(r_bounds)-1):
        for j in range(len(c_bounds)-1):
            r1, r2 = r_bounds[i], r_bounds[i+1]
            c1, c2 = c_bounds[j], c_bounds[j+1]
            
            # Adjust to exclude divider lines
            sub_r1 = r1 + (1 if i > 0 else 0)
            sub_r2 = r2 - (1 if i < len(r_bounds)-2 else 0)
            sub_c1 = c1 + (1 if j > 0 else 0)
            sub_c2 = c2 - (1 if j < len(c_bounds)-2 else 0)
            
            # Find seeds in this region
            region = grid[r1:r2, c1:c2]
            bg_color = np.bincount(region.flatten()).argmax()
            seeds = []
            for rr in range(r1, r2):
                for cc in range(c1, c2):
                    if grid[rr, cc] != bg_color and (rr not in row_divs) and (cc not in col_divs):
                        seeds.append(((rr, cc), grid[rr, cc]))
            
            if not seeds:
                # Fill with background or corner color if logic dictates
                output[r1:r2, c1:c2] = grid[r1, c1]
                continue

            # Expansion Logic: Concentric rings
            # Determine rings based on distance from region boundary
            h = r2 - r1
            w = c2 - c1
            num_rings = (min(h, w) + 1) // 2
            
            # Map seeds to rings
            ring_colors = {}
            for (sr, sc), sc_val in seeds:
                dist = min(sr - r1, r2 - 1 - sr, sc - c1, c2 - 1 - sc)
                ring_colors[dist] = sc_val
            
            # Determine outer color (corner seed or existing)
            outer_color = grid[r1, c1]
            
            current_color = outer_color
            for dist in range(num_rings):
                if dist in ring_colors:
                    current_color = ring_colors[dist]
                
                # Fill the ring
                for rr in range(r1 + dist, r2 - dist):
                    for cc in range(c1 + dist, c2 - dist):
                        # Only fill the "border" of the current inner rectangle
                        if rr == r1 + dist or rr == r2 - 1 - dist or \
                           cc == c1 + dist or cc == c2 - 1 - dist:
                            output[rr, cc] = current_color

    return output.tolist()


# ======================================================================
# Gemini iter 3 -- wrong_training
# training_pass=0/3  training_diff_total=692  test_diff_total=1573  test_label=FALSE_CONFIDENT_SUBMIT
# stated_rule: (none)
# source: Model Results/Gemini/13e47133/iter_3_response.py
# ======================================================================
import numpy as np

def solve(input_grid):
    grid = np.array(input_grid)
    rows, cols = grid.shape
    output = grid.copy()

    # 1. Identify Divider Lines
    row_divs = []
    for r in range(rows):
        unique, counts = np.unique(grid[r, :], return_counts=True)
        # A divider row is mostly one color and spans the width
        if counts.max() >= cols * 0.7:
            row_divs.append(r)
            
    col_divs = []
    for c in range(cols):
        unique, counts = np.unique(grid[:, c], return_counts=True)
        # A divider col is mostly one color and spans the height
        if counts.max() >= rows * 0.7:
            col_divs.append(c)

    # 2. Define Regions (Cells)
    r_bounds = sorted(list(set([0, rows] + row_divs + [r + 1 for r in row_divs])))
    c_bounds = sorted(list(set([0, cols] + col_divs + [c + 1 for c in col_divs])))
    
    # Filter bounds to only include the starts and ends of open regions
    regions_r = []
    for i in range(len(r_bounds)-1):
        if r_bounds[i] not in row_divs:
            regions_r.append((r_bounds[i], r_bounds[i+1]))
            
    regions_c = []
    for i in range(len(c_bounds)-1):
        if c_bounds[i] not in col_divs:
            regions_c.append((c_bounds[i], c_bounds[i+1]))

    # 3. Process each Cell
    for (r1, r2) in regions_r:
        for (c1, c2) in regions_c:
            region = grid[r1:r2, c1:c2]
            if region.size == 0: continue
            
            # Find background (most common color in the original region)
            bg_color = np.bincount(region.flatten()).argmax()
            
            # Map seeds to their ring depth
            ring_colors = {}
            for rr in range(r1, r2):
                for cc in range(c1, c2):
                    val = grid[rr, cc]
                    if val != bg_color:
                        # Depth is distance to nearest edge of the cell
                        depth = min(rr - r1, r2 - 1 - rr, cc - c1, c2 - 1 - cc)
                        ring_colors[depth] = val
            
            # Corner defines the initial/outermost color if no depth-0 seed
            current_color = grid[r1, c1]
            
            h, w = r2 - r1, c2 - c1
            max_depth = (min(h, w) + 1) // 2
            
            for d in range(max_depth):
                if d in ring_colors:
                    current_color = ring_colors[d]
                
                # Apply color to the ring at depth d
                for rr in range(r1 + d, r2 - d):
                    for cc in range(c1 + d, c2 - d):
                        if rr == r1 + d or rr == r2 - 1 - d or \
                           cc == c1 + d or cc == c2 - 1 - d:
                            output[rr, cc] = current_color
                            
    return output.tolist()


# ======================================================================
# Gemini iter 4 -- wrong_training
# training_pass=0/3  training_diff_total=692  test_diff_total=1573  test_label=FALSE_CONFIDENT_SUBMIT
# stated_rule: (none)
# source: Model Results/Gemini/13e47133/iter_4_response.py
# ======================================================================
import numpy as np

def solve(input_grid):
    grid = np.array(input_grid)
    rows, cols = grid.shape
    output_grid = grid.copy()

    # 1. Identify the "Skeleton/Divider" colors.
    # These are colors that form continuous lines (horizontal/vertical).
    divider_colors = []
    for color in range(1, 10):
        mask = (grid == color)
        # Check if color forms a line longer than 3 pixels
        if np.sum(mask) > max(rows, cols) * 0.5:
            divider_colors.append(color)

    # 2. Identify "Seed" pixels and their locations.
    # Seeds are typically singular pixels that define a region's color.
    seeds = []
    for r in range(rows):
        for c in range(cols):
            color = grid[r, c]
            if color != 0 and color not in divider_colors:
                # Check if it's a "lonely" pixel or a corner
                seeds.append(((r, c), color))

    # 3. Expansion Logic: Fill regions based on proximity to dividers and seeds.
    # We use a flood-fill approach that respects the skeleton boundaries.
    def get_bounds(r, c, skeleton_mask):
        # Find the rectangular bounds for a seed until hitting skeleton
        r_start, r_end = r, r
        c_start, c_end = c, c
        
        while r_start > 0 and not skeleton_mask[r_start-1, c]: r_start -= 1
        while r_end < rows-1 and not skeleton_mask[r_end+1, c]: r_end += 1
        while c_start > 0 and not skeleton_mask[r, c_start-1]: c_start -= 1
        while c_end < cols-1 and not skeleton_mask[r, c_end+1]: c_end += 1
        return r_start, r_end, c_start, c_end

    skeleton_mask = np.zeros_like(grid, dtype=bool)
    for dc in divider_colors:
        skeleton_mask |= (grid == dc)

    # Process seeds from outermost to innermost (heuristic)
    seeds.sort(key=lambda x: (min(x[0][0], rows-x[0][0]) + min(x[0][1], cols-x[0][1])))

    for (r, c), color in seeds:
        r_start, r_end, c_start, c_end = get_bounds(r, c, skeleton_mask)
        # Fill the determined rectangle
        for i in range(r_start, r_end + 1):
            for j in range(c_start, c_end + 1):
                # Only fill if it was originally the background color (usually 1 or 4)
                # or if we are refining a previously filled area.
                if not skeleton_mask[i, j]:
                    output_grid[i, j] = color

    # 4. Final Polish: Handle specific "Frame" logic found in the pairs
    # (Drawing concentric boxes if the seed is a corner of a sub-region)
    for (r, c), color in seeds:
        if (r == 0 or r == rows-1 or c == 0 or c == cols-1 or 
            (r > 0 and skeleton_mask[r-1, c]) or (r < rows-1 and skeleton_mask[r+1, c])):
            
            r_s, r_e, c_s, c_e = get_bounds(r, c, skeleton_mask)
            # Check if this seed should form a frame
            # If the seed is at a corner of its bounds, fill the outer edge
            output_grid[r_s:r_e+1, c_s:c_e+1] = color

    return output_grid.tolist()


# ======================================================================
# Grok iter 1 -- wrong_training
# training_pass=2/3  training_diff_total=4  test_diff_total=88  test_label=FALSE_CONFIDENT_SUBMIT
# stated_rule: (none)
# source: Model Results/Grok/13e47133/iter_1_response.py
# ======================================================================
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


# ======================================================================
# Grok_NoTrans iter 1 -- wrong_training
# training_pass=2/3  training_diff_total=4  test_diff_total=88  test_label=FALSE_CONFIDENT_SUBMIT
# stated_rule: (none)
# source: Model Results/Grok_NoTrans/13e47133/iter_1_response.py
# ======================================================================
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
