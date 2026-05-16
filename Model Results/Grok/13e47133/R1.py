def solve(input_grid):
    if not input_grid or not input_grid[0]:
        return []
    rows = len(input_grid)
    cols = len(input_grid[0])
    flat = [item for row in input_grid for item in row]
    count = Counter(flat)
    bg = count.most_common(1)[0][0]
    if len(count) > 1:
        barrier = count.most_common(2)[1][0]
    else:
        barrier = bg
    visited = [[False] * cols for _ in range(rows)]
    regions = []
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] != barrier and not visited[i][j]:
                minr, maxr, minc, maxc = i, i, j, j
                stack = [(i, j)]
                visited[i][j] = True
                while stack:
                    r, c = stack.pop()
                    minr = min(minr, r)
                    maxr = max(maxr, r)
                    minc = min(minc, c)
                    maxc = max(maxc, c)
                    for dr, dc in dirs:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols and input_grid[nr][nc] != barrier and not visited[nr][nc]:
                            visited[nr][nc] = True
                            stack.append((nr, nc))
                regions.append((minr, maxr, minc, maxc))
    output = [row[:] for row in input_grid]
    for r1, r2, c1, c2 in regions:
        corner_info = [
            (r1, c1, 1, 1),  # tl
            (r1, c2, 1, -1), # tr
            (r2, c1, -1, 1), # bl
            (r2, c2, -1, -1) # br
        ]
        best_seq = []
        best_num_nonbg = -1
        best_len = -1
        for sr, sc, dr, dc in corner_info:
            seq = []
            for k in range(100):
                rr = sr + k * dr
                cc = sc + k * dc
                if not (r1 <= rr <= r2 and c1 <= cc <= c2):
                    break
                colr = input_grid[rr][cc]
                if k == 0:
                    seq.append(colr)
                elif colr != bg:
                    seq.append(colr)
                else:
                    break
            num_nonbg = sum(1 for x in seq if x != bg)
            curr_len = len(seq)
            if num_nonbg > best_num_nonbg or (num_nonbg == best_num_nonbg and curr_len > best_len):
                best_num_nonbg = num_nonbg
                best_len = curr_len
                best_seq = seq
        cycle = best_seq if best_seq else [bg]
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if input_grid[r][c] == barrier:
                    continue
                dist_top = r - r1
                dist_bot = r2 - r
                dist_left = c - c1
                dist_right = c2 - c
                layer = min(dist_top, dist_bot, dist_left, dist_right)
                col_idx = layer % len(cycle)
                output[r][c] = cycle[col_idx]
    return output