def infer_T(input_grid):
    """Find each solid rectangle of 4s; mark its interior cells.
    The larger rectangle (by area) gets interior color 2, the smaller gets 1."""
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 4 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    if not (0 <= cr < H and 0 <= cc < W):
                        continue
                    if seen[cr][cc] or input_grid[cr][cc] != 4:
                        continue
                    seen[cr][cc] = True
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((cr + dr, cc + dc))
                comps.append(cells)

    sizes = [len(cs) for cs in comps]
    max_size = max(sizes) if sizes else 0

    T = {}
    for cs, sz in zip(comps, sizes):
        rs = [p[0] for p in cs]
        cstmp = [p[1] for p in cs]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cstmp), max(cstmp)
        color = 2 if sz == max_size else 1
        for (pr, pc) in cs:
            if r0 < pr < r1 and c0 < pc < c1:
                T[(pr, pc)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
