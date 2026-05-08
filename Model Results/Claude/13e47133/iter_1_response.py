def solve(input_grid):
    from collections import Counter, deque

    H = len(input_grid)
    W = len(input_grid[0])

    counts = Counter()
    for r in range(H):
        for c in range(W):
            counts[input_grid[r][c]] += 1

    bg = counts.most_common(1)[0][0]
    candidates = [(cnt, col) for col, cnt in counts.items() if col != bg]
    candidates.sort(reverse=True)
    barrier = candidates[0][1]

    visited = [[False]*W for _ in range(H)]
    regions = []

    def bfs_region(sr, sc):
        q = deque([(sr, sc)])
        visited[sr][sc] = True
        cells = []
        while q:
            r, c = q.popleft()
            cells.append((r, c))
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < H and 0 <= nc < W and not visited[nr][nc] and input_grid[nr][nc] != barrier:
                    visited[nr][nc] = True
                    q.append((nr, nc))
        return cells

    for r in range(H):
        for c in range(W):
            if not visited[r][c] and input_grid[r][c] != barrier:
                regions.append(bfs_region(r, c))

    output = [row[:] for row in input_grid]

    for region_cells in regions:
        cell_set = set(region_cells)

        dist = {}
        q = deque()

        for r, c in region_cells:
            is_boundary = False
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r+dr, c+dc
                    if nr < 0 or nr >= H or nc < 0 or nc >= W or input_grid[nr][nc] == barrier:
                        is_boundary = True
                        break
                if is_boundary:
                    break
            if is_boundary:
                dist[(r,c)] = 0
                q.append((r,c))

        while q:
            r, c = q.popleft()
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r+dr, c+dc
                    if (nr, nc) in cell_set and (nr, nc) not in dist:
                        dist[(nr,nc)] = dist[(r,c)] + 1
                        q.append((nr, nc))

        markers = {}
        for r, c in region_cells:
            color = input_grid[r][c]
            if color != bg and color != barrier:
                d = dist.get((r,c), 0)
                markers[d] = color

        if not markers:
            continue

        max_d = max(markers.keys())
        seq = []
        for d in range(max_d + 1):
            seq.append(markers.get(d, bg))

        seq_len = len(seq)
        for r, c in region_cells:
            d = dist.get((r,c), 0)
            output[r][c] = seq[d % seq_len]

    return output