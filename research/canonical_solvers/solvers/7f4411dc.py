def infer_T(input_grid):
    """Latent mask: for each connected blob of the foreground color, keep only
    its maximal solid filled rectangle (clearing everything else to background).
    Single-cell noise blobs (max rect area < 2) are erased entirely."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    fg = None
    for v in counts:
        if v != bg:
            fg = v
    T = [[None] * W for _ in range(H)]
    if fg is None:
        return T

    seen = set()
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != fg or (r, c) in seen:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                x, y = stack.pop()
                if (x, y) in seen or not (0 <= x < H and 0 <= y < W):
                    continue
                if input_grid[x][y] != fg:
                    continue
                seen.add((x, y))
                cells.append((x, y))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    stack.append((x + dr, y + dc))

            cset = set(cells)
            rs = [x for x, y in cells]
            ys = [y for x, y in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(ys), max(ys)

            best = None
            best_area = 0
            for a in range(r0, r1 + 1):
                for b in range(a, r1 + 1):
                    for u in range(c0, c1 + 1):
                        for w in range(u, c1 + 1):
                            if all((xx, yy) in cset
                                   for xx in range(a, b + 1)
                                   for yy in range(u, w + 1)):
                                area = (b - a + 1) * (w - u + 1)
                                if area > best_area:
                                    best_area = area
                                    best = (a, b, u, w)

            # clear the whole blob, then redraw its dominant solid rectangle
            for (x, y) in cells:
                T[x][y] = bg
            if best is not None and best_area >= 2:
                a, b, u, w = best
                for xx in range(a, b + 1):
                    for yy in range(u, w + 1):
                        T[xx][yy] = fg
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
