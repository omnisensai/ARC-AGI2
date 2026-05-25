def _background(grid):
    # Most common color is background; border color (forms full frame) treated as bg too.
    H, W = len(grid), len(grid[0])
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    bgset = {bg}
    # detect a full border frame color
    border = grid[0][0]
    if all(grid[0][c] == border for c in range(W)) and \
       all(grid[H-1][c] == border for c in range(W)) and \
       all(grid[r][0] == border for r in range(H)) and \
       all(grid[r][W-1] == border for r in range(H)) and border != bg:
        bgset.add(border)
    return bg, bgset


def _objects(grid, ignore):
    H, W = len(grid), len(grid[0])
    seen = set()
    objs = []
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v in ignore or (r, c) in seen:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                a, b = stack.pop()
                if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                    continue
                if grid[a][b] != v:
                    continue
                seen.add((a, b))
                cells.append((a, b))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr or dc:
                            stack.append((a + dr, b + dc))
            objs.append((v, cells))
    return objs


def infer_T(input_grid):
    """Latent mask: gravity-pack objects to the bottom, left-to-right by size."""
    H, W = len(input_grid), len(input_grid[0])
    bg, ignore = _background(input_grid)
    objs = _objects(input_grid, ignore)
    # sort by cell count ascending; ties keep stable order by original top-left
    decorated = []
    for v, cells in objs:
        rmin = min(a for a, b in cells)
        cmin = min(b for a, b in cells)
        decorated.append((len(cells), rmin, cmin, v, cells))
    decorated.sort(key=lambda x: (x[0], x[1], x[2]))

    T = {}
    col = 0
    for size, _, _, v, cells in decorated:
        cmin = min(b for a, b in cells)
        rmax = max(a for a, b in cells)
        w = max(b for a, b in cells) - cmin + 1
        for a, b in cells:
            rr = (H - 1) + (a - rmax)
            cc = col + (b - cmin)
            T[(rr, cc)] = v
        col += w
    return T, bg


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    mask, bg = T
    out = [[bg] * W for _ in range(H)]
    for (r, c), v in mask.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
