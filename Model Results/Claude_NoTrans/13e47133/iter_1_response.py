import collections
from collections import deque

def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])

    color_count = collections.Counter()
    for r in range(rows):
        for c in range(cols):
            color_count[input_grid[r][c]] += 1
    background = color_count.most_common(1)[0][0]

    non_bg_colors = [c for c in color_count if c != background]

    def count_line_cells(color):
        cells_in_lines = set()
        for r in range(rows):
            run_start = None
            for c in range(cols + 1):
                if c < cols and input_grid[r][c] == color:
                    if run_start is None: run_start = c
                else:
                    if run_start is not None:
                        if c - run_start >= 3:
                            for cc in range(run_start, c):
                                cells_in_lines.add((r, cc))
                        run_start = None
        for c in range(cols):
            run_start = None
            for r in range(rows + 1):
                if r < rows and input_grid[r][c] == color:
                    if run_start is None: run_start = r
                else:
                    if run_start is not None:
                        if r - run_start >= 3:
                            for rr in range(run_start, r):
                                cells_in_lines.add((rr, c))
                        run_start = None
        return len(cells_in_lines)

    barrier = max(non_bg_colors, key=count_line_cells) if non_bg_colors else background

    visited = [[False]*cols for _ in range(rows)]
    components = []

    def bfs_component(start_r, start_c):
        comp = []
        queue = deque([(start_r, start_c)])
        visited[start_r][start_c] = True
        while queue:
            r, c = queue.popleft()
            comp.append((r, c))
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc] and input_grid[nr][nc] != barrier:
                        visited[nr][nc] = True
                        queue.append((nr, nc))
        return comp

    for r in range(rows):
        for c in range(cols):
            if not visited[r][c] and input_grid[r][c] != barrier:
                comp = bfs_component(r, c)
                components.append(comp)

    output = [row[:] for row in input_grid]

    for comp in components:
        comp_set = set(comp)

        min_r = min(r for r, c in comp)
        max_r = max(r for r, c in comp)
        min_c = min(c for r, c in comp)
        max_c = max(c for r, c in comp)

        boundary = set()
        for r, c in comp:
            is_boundary = (r == 0 or r == rows - 1 or c == 0 or c == cols - 1)
            if not is_boundary:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0: continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols and input_grid[nr][nc] == barrier:
                            is_boundary = True
                            break
                    if is_boundary: break
            if is_boundary:
                boundary.add((r, c))

        dist = {}
        queue = deque()
        for r, c in boundary:
            dist[(r, c)] = 0
            queue.append((r, c))
        while queue:
            r, c = queue.popleft()
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in comp_set and (nr, nc) not in dist:
                        dist[(nr, nc)] = dist[(r, c)] + 1
                        queue.append((nr, nc))

        def read_diagonal(cr, cc, dr, dc):
            if (cr, cc) not in comp_set:
                return []
            markers = []
            seen_non_bg = False
            r, c = cr, cc
            while (r, c) in comp_set:
                val = input_grid[r][c]
                if val != background:
                    seen_non_bg = True
                if val == background and seen_non_bg:
                    break
                markers.append(val)
                r += dr
                c += dc
            if len(markers) >= 1 and markers[0] != background:
                return markers
            if len(markers) >= 2 and markers[1] != background:
                return markers
            return []

        corners = [
            (min_r, min_c, 1, 1),
            (min_r, max_c, 1, -1),
            (max_r, min_c, -1, 1),
            (max_r, max_c, -1, -1),
        ]

        best_markers = [background]
        for cr, cc, dr, dc in corners:
            if (cr, cc) not in comp_set:
                continue
            markers = read_diagonal(cr, cc, dr, dc)
            if not markers:
                continue
            has_non_bg = any(m != background for m in markers)
            best_has_non_bg = any(m != background for m in best_markers)
            if has_non_bg and (not best_has_non_bg or len(markers) > len(best_markers)):
                best_markers = markers

        n = len(best_markers)
        for r, c in comp:
            d = dist.get((r, c), 0)
            output[r][c] = best_markers[d % n]

    return output
