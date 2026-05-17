"""
Puzzle: d6542281
Rule name: complete_partial_shapes_from_templates

Transformation rule:
For each cluster that is a translated subset of a larger complete template cluster, fill in the missing cells using the template's pattern aligned to the partial fragment.

Validation: all 5/5 pairs (training + test) of the source puzzle pass.
Source: agent-generated R1 code (Claude general-purpose, seed prompt v1).
Judge consensus: 5/5 LLM judges produced this exact rule name.
"""
from collections import Counter, deque

def solve(input_grid):
    grid = [row[:] for row in input_grid]
    H = len(grid)
    W = len(grid[0])

    cnt = Counter()
    for r in range(H):
        for c in range(W):
            cnt[grid[r][c]] += 1
    bg = cnt.most_common(1)[0][0]

    visited = [[False]*W for _ in range(H)]
    components = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not visited[r][c]:
                q = deque([(r,c)])
                visited[r][c] = True
                comp = []
                while q:
                    y,x = q.popleft()
                    comp.append((y,x,grid[y][x]))
                    for dy in (-1,0,1):
                        for dx in (-1,0,1):
                            if dy==0 and dx==0: continue
                            ny,nx = y+dy, x+dx
                            if 0<=ny<H and 0<=nx<W and not visited[ny][nx] and grid[ny][nx]!=bg:
                                visited[ny][nx] = True
                                q.append((ny,nx))
                components.append(comp)

    def bbox(comp):
        rs = [c[0] for c in comp]
        cs = [c[1] for c in comp]
        return min(rs), min(cs), max(rs), max(cs)

    n = len(components)
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a,b):
        ra,rb = find(a), find(b)
        if ra != rb: parent[ra] = rb

    PROX = 2
    bboxes = [bbox(c) for c in components]
    for i in range(n):
        for j in range(i+1, n):
            r1a,c1a,r2a,c2a = bboxes[i]
            r1b,c1b,r2b,c2b = bboxes[j]
            dr = max(0, max(r1a,r1b) - min(r2a,r2b))
            dc = max(0, max(c1a,c1b) - min(c2a,c2b))
            if dr <= PROX and dc <= PROX:
                union(i,j)

    clusters = {}
    for i in range(n):
        rr = find(i)
        clusters.setdefault(rr, []).append(i)

    cluster_info = []
    for k, idxs in clusters.items():
        cells = []
        for i in idxs:
            cells.extend(components[i])
        colors = frozenset(c[2] for c in cells)
        cluster_info.append({'idx': k, 'comps': idxs, 'cells': cells, 'colors': colors})

    def normalize(cells):
        rs = [c[0] for c in cells]
        cs = [c[1] for c in cells]
        mr, mc = min(rs), min(cs)
        return frozenset((r-mr, c-mc, v) for r,c,v in cells), mr, mc

    norm_patterns = []
    for ci in cluster_info:
        pat, mr, mc = normalize(ci['cells'])
        norm_patterns.append((pat, mr, mc))

    def is_subset_under_translation(small_pat, large_pat):
        small_list = list(small_pat)
        if not small_list: return None
        s0 = small_list[0]
        for lc in large_pat:
            if lc[2] != s0[2]: continue
            off_r = lc[0] - s0[0]
            off_c = lc[1] - s0[1]
            shifted = frozenset((r+off_r, c+off_c, v) for r,c,v in small_pat)
            if shifted <= large_pat:
                return (off_r, off_c)
        return None

    is_partial = [False]*len(cluster_info)
    template_of = [None]*len(cluster_info)
    offset_of = [None]*len(cluster_info)
    for i, ci in enumerate(cluster_info):
        best_size = 0
        for j, cj in enumerate(cluster_info):
            if i == j: continue
            if len(cj['cells']) <= len(ci['cells']): continue
            if not ci['colors'].issubset(cj['colors']): continue
            off = is_subset_under_translation(norm_patterns[i][0], norm_patterns[j][0])
            if off is not None:
                if len(cj['cells']) > best_size:
                    best_size = len(cj['cells'])
                    template_of[i] = j
                    offset_of[i] = off
                    is_partial[i] = True

    output = [row[:] for row in grid]

    unique_colors = {color for color, c in cnt.items() if c == 1 and color != bg}

    template_indices = set()
    for i in range(len(cluster_info)):
        if is_partial[i]:
            template_indices.add(template_of[i])

    for partial_idx in range(len(cluster_info)):
        if not is_partial[partial_idx]:
            continue
        template_idx = template_of[partial_idx]
        off_r, off_c = offset_of[partial_idx]
        partial_pat, p_mr, p_mc = norm_patterns[partial_idx]
        template_pat, t_mr, t_mc = norm_patterns[template_idx]
        for DR, DC, v in template_pat:
            gr = DR - off_r + p_mr
            gc = DC - off_c + p_mc
            if 0 <= gr < H and 0 <= gc < W:
                output[gr][gc] = v

    for color in unique_colors:
        for r in range(H):
            for c in range(W):
                if grid[r][c] == color:
                    for ti in template_indices:
                        cells = cluster_info[ti]['cells']
                        if any(cr == r and cc == c for cr,cc,_ in cells):
                            output[r][c] = bg
                            break

    return output
