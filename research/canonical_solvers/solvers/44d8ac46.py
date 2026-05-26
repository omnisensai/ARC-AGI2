def _components(g):
    """Connected components of color-5 cells (8-connectivity)."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == 5 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W:
                        continue
                    if seen[y][x] or g[y][x] != 5:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy or dx:
                                stack.append((y + dy, x + dx))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    """Latent mask: dict {(r,c): 2} for cells to recolor.

    Each box is a connected blob of 5s with a hollow interior. The hole
    region (0-cells strictly inside the bounding box) is filled with 2
    iff those holes form a solid SQUARE block.
    """
    g = input_grid
    H, W = len(g), len(g[0])
    T = {}
    for comp in _components(g):
        rs = [y for y, _ in comp]
        cs = [x for _, x in comp]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        # interior = cells strictly inside the bounding box
        interior = [(y, x) for y in range(r0 + 1, r1)
                    for x in range(c0 + 1, c1)]
        holes = [(y, x) for y, x in interior if g[y][x] == 0]
        if not holes:
            continue
        hr = [y for y, _ in holes]
        hc = [x for _, x in holes]
        hr0, hr1, hc0, hc1 = min(hr), max(hr), min(hc), max(hc)
        hh = hr1 - hr0 + 1
        hw = hc1 - hc0 + 1
        if hh != hw:
            continue  # hole region must be square
        holeset = set(holes)
        solid = all((y, x) in holeset
                    for y in range(hr0, hr1 + 1)
                    for x in range(hc0, hc1 + 1))
        if not solid:
            continue  # hole region must be a solid (filled) block
        for y, x in holes:
            T[(y, x)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
