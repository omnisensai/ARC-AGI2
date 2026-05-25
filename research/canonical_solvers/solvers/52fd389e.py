def infer_T(input_grid):
    """Latent mask: for each 4-rectangle, draw a border of its inner noise color,
    with thickness equal to the number of noise cells inside the rectangle."""
    H, W = len(input_grid), len(input_grid[0])
    grid = input_grid
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 4 and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and grid[nr][nc] == 4 and not seen[nr][nc]:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(cells)

    T = {}
    for cells in comps:
        rs = [p[0] for p in cells]
        cs = [p[1] for p in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        ncolor = None
        ncount = 0
        for rr in range(r0, r1 + 1):
            for cc in range(c0, c1 + 1):
                v = grid[rr][cc]
                if v not in (0, 4):
                    ncolor = v
                    ncount += 1
        if ncolor is None:
            continue
        t = ncount  # border thickness = number of noise cells
        for rr in range(r0 - t, r1 + t + 1):
            for cc in range(c0 - t, c1 + t + 1):
                if 0 <= rr < H and 0 <= cc < W:
                    if rr < r0 or rr > r1 or cc < c0 or cc > c1:
                        T[(rr, cc)] = ncolor
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
