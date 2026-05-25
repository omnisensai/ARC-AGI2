from collections import Counter, deque

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def infer_T(input_grid):
    """Compute a latent transformation mask (2D None/int grid).

    The grid is partitioned by a single 'divider' color (2nd most common) into
    connected regions of non-divider cells. Each region is filled with
    concentric rectangular rings (Chebyshev distance from the region's
    boundary). The ring colors come from the marker cells inside the region:
    a marker at Chebyshev ring distance k sets the color of ring k. Rings
    without a marker default to the background color, and the color sequence
    repeats (cycles) outward to cover the whole region.
    """
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter(v for row in input_grid for v in row)
    mc = cnt.most_common()
    bg = mc[0][0]
    divider = mc[1][0] if len(mc) > 1 else None

    T = [[None] * W for _ in range(H)]
    seen = [[False] * W for _ in range(H)]

    for sr in range(H):
        for sc in range(W):
            if seen[sr][sc] or input_grid[sr][sc] == divider:
                continue
            # 4-connected component of non-divider cells = one region
            comp = []
            q = deque([(sr, sc)])
            seen[sr][sc] = True
            while q:
                r, c = q.popleft()
                comp.append((r, c))
                for dr, dc in N4:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < H and 0 <= nc < W and not seen[nr][nc]
                            and input_grid[nr][nc] != divider):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            compset = set(comp)

            markers = [(r, c) for (r, c) in comp if input_grid[r][c] != bg]
            if not markers:
                continue

            # Chebyshev ring distance via 8-connected BFS from the region border
            dist = {}
            bq = deque()
            for (r, c) in comp:
                for dr, dc in N8:
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < H and 0 <= nc < W) or (nr, nc) not in compset:
                        dist[(r, c)] = 0
                        bq.append((r, c))
                        break
            while bq:
                r, c = bq.popleft()
                for dr, dc in N8:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in compset and (nr, nc) not in dist:
                        dist[(nr, nc)] = dist[(r, c)] + 1
                        bq.append((nr, nc))

            # ring color sequence from markers, gaps -> background, then cycle
            ringcol = {}
            for (r, c) in markers:
                ringcol[dist[(r, c)]] = input_grid[r][c]
            maxd = max(ringcol)
            seq = [ringcol.get(k, bg) for k in range(maxd + 1)]
            n = len(seq)

            for (r, c) in comp:
                T[r][c] = seq[dist[(r, c)] % n]

    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
