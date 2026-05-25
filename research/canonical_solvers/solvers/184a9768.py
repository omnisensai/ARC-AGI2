from collections import deque, Counter


def _bg(g):
    c = Counter(v for row in g for v in row)
    return c.most_common(1)[0][0]


def _components(pred, H, W):
    seen = [[False] * W for _ in range(H)]
    res = []
    for r in range(H):
        for c in range(W):
            if pred(r, c) and not seen[r][c]:
                q = deque([(r, c)])
                seen[r][c] = True
                cells = []
                while q:
                    y, x = q.popleft()
                    cells.append((y, x))
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and pred(ny, nx) and not seen[ny][nx]:
                            seen[ny][nx] = True
                            q.append((ny, nx))
                res.append(cells)
    return res


def _holes(g, cells, bg):
    # background cells enclosed inside the bounding box of a container component
    H, W = len(g), len(g[0])
    rs = [y for y, x in cells]
    cs = [x for y, x in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    outside = set()
    q = deque()
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r == r0 or r == r1 or c == c0 or c == c1) and g[r][c] == bg and (r, c) not in outside:
                outside.add((r, c))
                q.append((r, c))
    while q:
        y, x = q.popleft()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = y + dy, x + dx
            if r0 <= ny <= r1 and c0 <= nx <= c1 and g[ny][nx] == bg and (ny, nx) not in outside:
                outside.add((ny, nx))
                q.append((ny, nx))
    return set((r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
               if g[r][c] == bg and (r, c) not in outside)


def infer_T(input_grid):
    """Infer the latent fill mask.

    Structure of the puzzle: some non-background colors form hollow "container"
    shapes (a blob with one or more enclosed rectangular cavities); other colors
    form solid rectangular "key" pieces scattered on the canvas, plus single-cell
    noise. The transformation erases everything except the containers, and fills
    each enclosed cavity with the key whose rectangle exactly matches it. Keys are
    placed largest-first into the enclosed hole cells of each container.

    Returns a dict {(r,c): new_color}. Cells not present keep their input value
    only if they belong to a container; all other cells are cleared to background.
    """
    g = input_grid
    H, W = len(g), len(g[0])
    bg = _bg(g)

    keys = []
    containers = []
    for col in set(v for row in g for v in row if v != bg):
        for cells in _components(lambda r, c, col=col: g[r][c] == col, H, W):
            rs = [y for y, x in cells]
            cs = [x for y, x in cells]
            h = max(rs) - min(rs) + 1
            w = max(cs) - min(cs) + 1
            if len(cells) == h * w:
                keys.append((col, h, w))
            else:
                containers.append((col, cells))

    T = {}
    # 1) clear the whole canvas to background
    for r in range(H):
        for c in range(W):
            T[(r, c)] = bg
    # 2) redraw container cells
    container_cells = set()
    for col, cells in containers:
        for y, x in cells:
            T[(y, x)] = col
            container_cells.add((y, x))

    # 3) fill enclosed cavities with matching keys (largest first)
    order = sorted(range(len(keys)), key=lambda i: -keys[i][1] * keys[i][2])
    for col, cells in containers:
        remaining = _holes(g, cells, bg)
        used = [False] * len(keys)
        for ki in order:
            if used[ki]:
                continue
            kc, kh, kw = keys[ki]
            placed = False
            rows = sorted(set(r for r, c in remaining))
            cols = sorted(set(c for r, c in remaining))
            for r0 in rows:
                for c0 in cols:
                    block = [(r0 + dr, c0 + dc) for dr in range(kh) for dc in range(kw)]
                    if all(p in remaining for p in block):
                        for p in block:
                            T[p] = kc
                            remaining.discard(p)
                        used[ki] = True
                        placed = True
                        break
                if placed:
                    break
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
