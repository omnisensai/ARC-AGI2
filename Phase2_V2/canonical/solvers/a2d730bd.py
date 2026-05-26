from collections import Counter


def infer_T(input_grid):
    """Infer a latent transformation mask {(r,c): new_color} from input structure.

    Structure: a uniform background, one (or more) solid rectangular block(s),
    and isolated single dots of the same color as a block. Each dot lies in the
    perpendicular span of its block but is offset on the other axis. The block
    "shoots" a double-headed arrow toward the dot:
      - a 3-cell tail bar (perpendicular) at the cell just outside the block edge,
      - an arm of color along the dot's aligned line up to the dot,
      - the dot itself erased (-> background), flanked by a 2-cell head bar and a
        single point one cell beyond the dot (the arrow tip).
    """
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter()
    for row in input_grid:
        for v in row:
            cnt[v] += 1
    bg = cnt.most_common(1)[0][0]

    # 4-connected components of non-background cells
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg and not seen[r][c]:
                col = input_grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W or seen[y][x]:
                        continue
                    if input_grid[y][x] != col:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((y + dy, x + dx))
                comps.append((col, cells))

    blocks = [(col, cells) for col, cells in comps if len(cells) > 1]
    dots = [(col, cells[0]) for col, cells in comps if len(cells) == 1]

    T = {}

    def put(rr, cc, color):
        if 0 <= rr < H and 0 <= cc < W:
            T[(rr, cc)] = color

    for dcol, (dr, dc) in dots:
        blk = next((cells for col, cells in blocks if col == dcol), None)
        if blk is None:
            continue
        rs = [y for y, x in blk]
        cs = [x for y, x in blk]
        rmin, rmax, cmin, cmax = min(rs), max(rs), min(cs), max(cs)

        # direction from block toward the dot
        if dc > cmax:
            d = (0, 1)
        elif dc < cmin:
            d = (0, -1)
        elif dr > rmax:
            d = (1, 0)
        elif dr < rmin:
            d = (-1, 0)
        else:
            continue
        dy, dx = d

        if dy == 0:
            # horizontal arrow: arm runs along the dot's row
            line = dr
            edge = cmax if dx > 0 else cmin
            adj = edge + dx
            # tail bar (one cell outside block edge)
            put(line - 1, adj, dcol)
            put(line, adj, dcol)
            put(line + 1, adj, dcol)
            # arm from tail toward dot (exclusive of dot)
            cc = adj
            while cc != dc:
                put(line, cc, dcol)
                cc += dx
            # head at dot: erase dot, flank, and point beyond
            put(dr, dc, bg)
            put(line - 1, dc, dcol)
            put(line + 1, dc, dcol)
            put(line, dc + dx, dcol)
        else:
            # vertical arrow: arm runs along the dot's column
            line = dc
            edge = rmax if dy > 0 else rmin
            adj = edge + dy
            put(adj, line - 1, dcol)
            put(adj, line, dcol)
            put(adj, line + 1, dcol)
            rr = adj
            while rr != dr:
                put(rr, line, dcol)
                rr += dy
            put(dr, dc, bg)
            put(dr, line - 1, dcol)
            put(dr, line + 1, dcol)
            put(dr + dy, line, dcol)

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
