def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    grid = input_grid

    # find connected components of color 5 (the rectangular blocks)
    seen = [[False] * W for _ in range(H)]
    blocks = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 5 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    if cr < 0 or cr >= H or cc < 0 or cc >= W:
                        continue
                    if seen[cr][cc] or grid[cr][cc] != 5:
                        continue
                    seen[cr][cc] = True
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((cr + dr, cc + dc))
                blocks.append(cells)

    T = {}
    for cells in blocks:
        rs = [p[0] for p in cells]
        cs = [p[1] for p in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        h = r1 - r0 + 1
        w = c1 - c0 + 1

        # corner markers sit diagonally just outside the block's corners
        tl = (r0 - 1, c0 - 1)
        tr = (r0 - 1, c1 + 1)
        bl = (r1 + 1, c0 - 1)
        br = (r1 + 1, c1 + 1)

        def colat(p):
            pr, pc = p
            if 0 <= pr < H and 0 <= pc < W:
                return grid[pr][pc]
            return 0

        ctl, ctr, cbl, cbr = colat(tl), colat(tr), colat(bl), colat(br)

        # clear the original corner markers
        for p in (tl, tr, bl, br):
            pr, pc = p
            if 0 <= pr < H and 0 <= pc < W and grid[pr][pc] not in (0, 5):
                T[(pr, pc)] = 0

        # paint the block: each quadrant takes its corresponding corner color
        hmid = h // 2
        wmid = w // 2
        for dr in range(h):
            for dc in range(w):
                top = dr < hmid
                left = dc < wmid
                if top and left:
                    col = ctl
                elif top and not left:
                    col = ctr
                elif not top and left:
                    col = cbl
                else:
                    col = cbr
                T[(r0 + dr, c0 + dc)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
