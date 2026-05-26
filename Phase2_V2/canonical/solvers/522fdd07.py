def _find_objects(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if a < 0 or a >= H or b < 0 or b >= W:
                        continue
                    if seen[a][b] or g[a][b] != col:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                rs = [x for x, _ in cells]
                cs = [y for _, y in cells]
                objs.append((col, min(rs), max(rs), min(cs), max(cs)))
    return objs


def infer_T(input_grid):
    """Latent mask: each solid square is resized about its center.

    Square side lengths cycle 1 -> 9 -> 7 -> 5 -> 3 -> 1 (shrink by one
    layer per side, with the smallest 1x1 wrapping up to the largest 9x9),
    keeping the same center. The mask records, for every cell that differs
    from the background, what its new value should be.
    """
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    T = {}
    objs = _find_objects(input_grid, bg)
    # First clear all current object cells to background.
    for col, r0, r1, c0, c1 in objs:
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if input_grid[r][c] == col:
                    T[(r, c)] = bg
    # Then draw the resized squares.
    for col, r0, r1, c0, c1 in objs:
        side = r1 - r0 + 1
        cr = (r0 + r1) // 2
        cc = (c0 + c1) // 2
        new_side = 9 if side == 1 else side - 2
        if new_side < 1:
            continue
        half = new_side // 2
        for r in range(cr - half, cr + half + 1):
            for c in range(cc - half, cc + half + 1):
                if 0 <= r < H and 0 <= c < W:
                    T[(r, c)] = col
    return T, bg


def apply_T(input_grid, T_bg):
    T, bg = T_bg
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
