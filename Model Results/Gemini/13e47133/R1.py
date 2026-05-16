from collections import Counter

def solve(input_grid):
    grid = [row[:] for row in input_grid]
    H = len(grid)
    W = len(grid[0])
    counts = Counter((c for r in grid for c in r))
    top2 = counts.most_common(2)
    BG = top2[0][0]
    BAR = top2[1][0]
    visited = set()
    components = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != BAR and (r, c) not in visited:
                comp = []
                q = [(r, c)]
                visited.add((r, c))
                while q:
                    curr_r, curr_c = q.pop(0)
                    comp.append((curr_r, curr_c))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = (curr_r + dr, curr_c + dc)
                        if 0 <= nr < H and 0 <= nc < W and (grid[nr][nc] != BAR) and ((nr, nc) not in visited):
                            visited.add((nr, nc))
                            q.append((nr, nc))
                components.append(comp)
    for comp in components:
        min_r = min((r for r, c in comp))
        max_r = max((r for r, c in comp))
        min_c = min((c for r, c in comp))
        max_c = max((c for r, c in comp))
        d_to_seed = {}
        max_seed_d = -1
        for r, c in comp:
            if grid[r][c] != BG:
                d = min(r - min_r, max_r - r, c - min_c, max_c - c)
                d_to_seed[d] = grid[r][c]
                if d > max_seed_d:
                    max_seed_d = d
        if not d_to_seed:
            continue
        seq = []
        for d in range(max_seed_d + 1):
            if d in d_to_seed:
                seq.append(d_to_seed[d])
            else:
                seq.append(BG)
        for r, c in comp:
            d = min(r - min_r, max_r - r, c - min_c, max_c - c)
            grid[r][c] = seq[d % len(seq)]
    return grid