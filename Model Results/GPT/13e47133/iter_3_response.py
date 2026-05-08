def solve(input_grid):
    from collections import Counter, deque

    grid = input_grid
    H, W = len(grid), len(grid[0])

    counts = Counter(v for row in grid for v in row)
    bg = counts.most_common(1)[0][0]

    non_bg_counts = Counter(v for row in grid for v in row if v != bg)
    wall = non_bg_counts.most_common(1)[0][0]

    virtual_h = []
    for r in range(H):
        c = 0
        while c < W:
            if grid[r][c] != wall:
                c += 1
                continue

            a = c
            while c < W and grid[r][c] == wall:
                c += 1
            b = c - 1

            if b - a + 1 >= 3:
                left_through = (
                    0 < r < H - 1
                    and grid[r - 1][a] == wall
                    and grid[r + 1][a] == wall
                )
                right_through = (
                    0 < r < H - 1
                    and grid[r - 1][b] == wall
                    and grid[r + 1][b] == wall
                )

                if left_through and b < W - 1:
                    virtual_h.append((r, a, W - 1))
                if right_through and a > 0:
                    virtual_h.append((r, 0, b))

    up = [[0] * W for _ in range(H)]
    left = [[0] * W for _ in range(H)]
    down = [[0] * W for _ in range(H)]
    right = [[0] * W for _ in range(H)]

    for r in range(H):
        for c in range(W):
            if grid[r][c] == wall:
                continue
            up[r][c] = 0 if r == 0 or grid[r - 1][c] == wall else up[r - 1][c] + 1
            left[r][c] = 0 if c == 0 or grid[r][c - 1] == wall else left[r][c - 1] + 1

    for r in range(H - 1, -1, -1):
        for c in range(W - 1, -1, -1):
            if grid[r][c] == wall:
                continue
            down[r][c] = 0 if r == H - 1 or grid[r + 1][c] == wall else down[r + 1][c] + 1
            right[r][c] = 0 if c == W - 1 or grid[r][c + 1] == wall else right[r][c + 1] + 1

    def depth(r, c):
        d = min(up[r][c], down[r][c], left[r][c], right[r][c])
        for rr, ca, cb in virtual_h:
            if ca <= c <= cb and r != rr:
                d = min(d, abs(r - rr) - 1)
        return d

    output_grid = [row[:] for row in grid]
    seen = [[False] * W for _ in range(H)]
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

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

            seed_by_depth = {}
            for r, c in cells:
                v = grid[r][c]
                if v != bg:
                    d = depth(r, c)
                    seed_by_depth[d] = v

            if not seed_by_depth:
                continue

            if 0 not in seed_by_depth:
                seed_by_depth[0] = bg

            max_known = max(seed_by_depth)
            pattern = []
            last = seed_by_depth[0]
            for d in range(max_known + 1):
                if d in seed_by_depth:
                    last = seed_by_depth[d]
                pattern.append(last)

            for r, c in cells:
                d = depth(r, c)
                output_grid[r][c] = pattern[d % len(pattern)]

    return output_grid