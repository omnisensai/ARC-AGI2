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