"""Fine-tuning mirror: 13e47133 / wrong_test.

Auto-generated from wrong_test.jsonl. Each entry below is one
attempt with metadata in the comment header.
"""


# ======================================================================
# Claude_NoTrans iter 1 -- wrong_test
# training_pass=3/3  training_diff_total=0  test_diff_total=336  test_label=FALSE_CONFIDENT_SUBMIT
# stated_rule: (none)
# source: Model Results/Claude_NoTrans/13e47133/iter_1_response.py
# ======================================================================
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


# ======================================================================
# GPT iter 3 -- wrong_test
# training_pass=3/3  training_diff_total=0  test_diff_total=124  test_label=FALSE_CONFIDENT_SUBMIT
# stated_rule: (none)
# source: Model Results/GPT/13e47133/iter_3_response.py
# ======================================================================
def solve(input_grid):
    from collections import Counter, deque, defaultdict

    grid = input_grid
    h, w = len(grid), len(grid[0])

    counts = Counter(v for row in grid for v in row)
    background = counts.most_common(1)[0][0]

    barrier = max((c for c in counts if c != background), key=lambda c: counts[c])

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

            comp_r0 = min(r for r, c in comp)
            comp_r1 = max(r for r, c in comp)
            comp_c0 = min(c for r, c in comp)
            comp_c1 = max(c for r, c in comp)

            comp_colors = {}
            for r, c in comp:
                val = grid[r][c]
                if val != background and val != barrier:
                    d = min(r - comp_r0, comp_r1 - r, c - comp_c0, comp_c1 - c)
                    comp_colors.setdefault(d, val)

            comp_cycle = None
            if comp_colors:
                m = max(comp_colors)
                comp_cycle = [background] * (m + 1)
                for d, val in comp_colors.items():
                    comp_cycle[d] = val

            runs_by_span = defaultdict(list)
            for r in sorted(set(r for r, c in comp)):
                c = 0
                while c < w:
                    while c < w and (r, c) not in comp_set:
                        c += 1
                    if c >= w:
                        break
                    l = c
                    while c < w and (r, c) in comp_set:
                        c += 1
                    runs_by_span[(l, c - 1)].append(r)

            rects = []
            for (c0, c1), rs in runs_by_span.items():
                rs.sort()
                a = b = rs[0]
                for r in rs[1:]:
                    if r == b + 1:
                        b = r
                    else:
                        rects.append((a, b, c0, c1))
                        a = b = r
                rects.append((a, b, c0, c1))

            rect_cycles = {}
            inherited = None

            for i, (r0, r1, c0, c1) in enumerate(rects):
                colors = {}
                for r in range(r0, r1 + 1):
                    for c in range(c0, c1 + 1):
                        val = grid[r][c]
                        if val != background and val != barrier:
                            d = min(r - r0, r1 - r, c - c0, c1 - c)
                            colors.setdefault(d, val)

                if colors:
                    m = max(colors)
                    cycle = [background] * (m + 1)
                    for d, val in colors.items():
                        cycle[d] = val
                    rect_cycles[i] = cycle
                    if inherited is None:
                        inherited = cycle

            if inherited is None:
                continue

            cell_rect = {}
            for i, (r0, r1, c0, c1) in enumerate(rects):
                for r in range(r0, r1 + 1):
                    for c in range(c0, c1 + 1):
                        cell_rect[(r, c)] = i

            for i, (r0, r1, c0, c1) in enumerate(rects):
                cycle = rect_cycles.get(i, inherited)
                period = len(cycle)

                for r in range(r0, r1 + 1):
                    for c in range(c0, c1 + 1):
                        d = min(r - r0, r1 - r, c - c0, c1 - c)
                        val = cycle[d % period]

                        # Do not let an artificial horizontal split turn a
                        # continuing vertical connector into an outer ring.
                        if (
                            comp_cycle
                            and d == 0
                            and 0 < r < h - 1
                            and (r - 1, c) in comp_set
                            and (r + 1, c) in comp_set
                            and (
                                cell_rect.get((r - 1, c)) != i
                                or cell_rect.get((r + 1, c)) != i
                            )
                        ):
                            cd = min(r - comp_r0, comp_r1 - r, c - comp_c0, comp_c1 - c)
                            cv = comp_cycle[cd % len(comp_cycle)]
                            if cv != background:
                                val = cv

                        out[r][c] = val

    return out
