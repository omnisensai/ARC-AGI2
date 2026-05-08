def solve(input_grid):
    from collections import Counter, deque

    grid = input_grid
    H, W = len(grid), len(grid[0])

    bg = Counter(v for row in grid for v in row).most_common(1)[0][0]
    non_bg = Counter(v for row in grid for v in row if v != bg)
    wall = non_bg.most_common(1)[0][0]

    output_grid = [row[:] for row in grid]
    seen = [[False] * W for _ in range(H)]
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def diag_pos(corner, rmin, rmax, cmin, cmax, k):
        if corner == 0:
            return rmin + k, cmin + k
        if corner == 1:
            return rmin + k, cmax - k
        if corner == 2:
            return rmax - k, cmin + k
        return rmax - k, cmax - k

    for sr in range(H):
        for sc in range(W):
            if seen[sr][sc] or grid[sr][sc] == wall:
                continue

            q = deque([(sr, sc)])
            seen[sr][sc] = True
            cells = []

            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < H and 0 <= nc < W
                        and not seen[nr][nc]
                        and grid[nr][nc] != wall
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))

            seeds = [(r, c, grid[r][c]) for r, c in cells if grid[r][c] != bg]
            if not seeds:
                continue

            rmin = min(r for r, c in cells)
            rmax = max(r for r, c in cells)
            cmin = min(c for r, c in cells)
            cmax = max(c for r, c in cells)
            cellset = set(cells)

            best = None
            for corner in range(4):
                ks = []
                bad = 0
                for r, c, _ in seeds:
                    k = None
                    if corner == 0 and r - rmin == c - cmin:
                        k = r - rmin
                    elif corner == 1 and r - rmin == cmax - c:
                        k = r - rmin
                    elif corner == 2 and rmax - r == c - cmin:
                        k = rmax - r
                    elif corner == 3 and rmax - r == cmax - c:
                        k = rmax - r
                    else:
                        bad += 1

                    if k is not None:
                        ks.append(k)

                score = (len(ks), -bad, -(max(ks) if ks else 999999))
                if best is None or score > best[0]:
                    best = (score, corner, ks)

            corner = best[1]
            max_k = max(best[2]) if best[2] else 0

            pattern = []
            for k in range(max_k + 1):
                r, c = diag_pos(corner, rmin, rmax, cmin, cmax, k)
                if (r, c) in cellset:
                    pattern.append(grid[r][c])
                else:
                    pattern.append(bg)

            if all(v == bg for v in pattern):
                continue

            for r, c in cells:
                ring = min(r - rmin, rmax - r, c - cmin, cmax - c)
                output_grid[r][c] = pattern[ring % len(pattern)]

    return output_grid