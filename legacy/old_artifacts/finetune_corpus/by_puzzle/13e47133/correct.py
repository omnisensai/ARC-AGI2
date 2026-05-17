"""Fine-tuning mirror: 13e47133 / correct.

Auto-generated from correct.jsonl. Each entry below is one
attempt with metadata in the comment header.
"""


# ======================================================================
# Gemini R2 -- correct
# training_pass=3/3  training_diff_total=0  test_diff_total=0  test_label=TRUE_SOLVE
# stated_rule: The grid is divided into independent chambers by barrier-colored walls. Each chamber is filled with concentric rings matching its exact contours. The color of each cell inside a chamber is determined by its Chebyshev distance to the chamber's boundary, cycling through the sequence of seed colors discovered at those corresponding depths.
# source: Model Results/Gemini/13e47133/R2.py
# ======================================================================
from collections import Counter, deque

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
                q = deque([(r, c)])
                visited.add((r, c))
                while q:
                    curr_r, curr_c = q.popleft()
                    comp.append((curr_r, curr_c))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = (curr_r + dr, curr_c + dc)
                        if 0 <= nr < H and 0 <= nc < W:
                            if grid[nr][nc] != BAR and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                q.append((nr, nc))
                components.append(comp)
    for comp in components:
        comp_set = set(comp)
        dist = {}
        q = deque()
        for r, c in comp:
            has_outside_neighbor = False
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = (r + dr, c + dc)
                    if not (0 <= nr < H and 0 <= nc < W) or (nr, nc) not in comp_set:
                        has_outside_neighbor = True
                        break
                if has_outside_neighbor:
                    break
            if has_outside_neighbor:
                dist[r, c] = 1
                q.append((r, c))
        while q:
            curr_r, curr_c = q.popleft()
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = (curr_r + dr, curr_c + dc)
                    if 0 <= nr < H and 0 <= nc < W and ((nr, nc) in comp_set):
                        if (nr, nc) not in dist:
                            dist[nr, nc] = dist[curr_r, curr_c] + 1
                            q.append((nr, nc))
        d_to_seed = {}
        max_seed_d = -1
        for r, c in comp:
            if grid[r][c] != BG:
                d = dist[r, c] - 1
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
            d = dist[r, c] - 1
            grid[r][c] = seq[d % len(seq)]
    return grid
