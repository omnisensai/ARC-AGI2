def _bg(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _find_blocks(grid, bg):
    """Return list of (color, r0, c0, r1, c1) for each connected non-bg block."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    blocks = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if rr < 0 or rr >= H or cc < 0 or cc >= W:
                        continue
                    if seen[rr][cc] or grid[rr][cc] != color:
                        continue
                    seen[rr][cc] = True
                    cells.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((rr + dr, cc + dc))
                rs = [x[0] for x in cells]
                cs = [x[1] for x in cells]
                blocks.append((color, min(rs), min(cs), max(rs), max(cs)))
    return blocks


def infer_T(input_grid):
    """Latent mask: dict {(r,c): color}. Corner blocks of the majority color
    slide diagonally toward the grid center by their own size; minority-color
    blocks stay where they are. The mask records the full redrawn block layout."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg(input_grid)
    blocks = _find_blocks(input_grid, bg)

    # majority color among the corner blocks
    colcount = {}
    for (col, r0, c0, r1, c1) in blocks:
        colcount[col] = colcount.get(col, 0) + 1
    maj = max(colcount, key=lambda c: (colcount[c], -c))

    T = {}
    for (col, r0, c0, r1, c1) in blocks:
        h = r1 - r0 + 1
        w = c1 - c0 + 1
        if col == maj:
            # slide diagonally inward by block size
            top = r0 < H / 2
            left = c0 < W / 2
            dr = h if top else -h
            dc = w if left else -w
            nr0, nc0 = r0 + dr, c0 + dc
        else:
            nr0, nc0 = r0, c0
        for rr in range(nr0, nr0 + h):
            for cc in range(nc0, nc0 + w):
                if 0 <= rr < H and 0 <= cc < W:
                    T[(rr, cc)] = col
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg(input_grid)
    out = [[bg] * W for _ in range(H)]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
