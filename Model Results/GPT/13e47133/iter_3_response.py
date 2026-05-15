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