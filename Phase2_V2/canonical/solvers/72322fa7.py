def infer_T(input_grid):
    """Latent mask: fragments of a complete shape are completed by stamping
    the matching template (matched by color) at the correct alignment."""
    H, W = len(input_grid), len(input_grid[0])

    # 8-connected components of nonzero cells
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0 and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                        continue
                    if input_grid[a][b] == 0:
                        continue
                    seen.add((a, b))
                    cells.append((a, b, input_grid[a][b]))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((a + dr, b + dc))
                comps.append(cells)

    # A complete template uses >=2 distinct colors (center + border);
    # a fragment uses a single color.
    templates = []
    fragments = []
    for cells in comps:
        if len(set(v for _, _, v in cells)) >= 2:
            templates.append(cells)
        else:
            fragments.append(cells)

    # Each color maps to the relative cell pattern of its template.
    color_to_template = {}
    for cells in templates:
        r0 = min(r for r, _, _ in cells)
        c0 = min(c for _, c, _ in cells)
        rel = [(r - r0, c - c0, v) for r, c, v in cells]
        for _, _, v in cells:
            color_to_template[v] = rel

    # Gather fragment cells per color.
    by_color = {}
    for frag in fragments:
        for r, c, v in frag:
            by_color.setdefault(v, []).append((r, c))

    T = {}  # latent mask: (r,c) -> color to overwrite
    for color, cells in by_color.items():
        rel = color_to_template.get(color)
        if rel is None:
            continue
        same = [(dr, dc) for dr, dc, v in rel if v == color]
        same_set = set(same)
        # offset differences between same-color template cells -> instance link
        valid_diffs = set((a[0] - b[0], a[1] - b[1]) for a in same for b in same)

        # cluster fragment cells of this color into per-instance groups
        parent = list(range(len(cells)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for i in range(len(cells)):
            for j in range(i + 1, len(cells)):
                d = (cells[i][0] - cells[j][0], cells[i][1] - cells[j][1])
                if d in valid_diffs:
                    parent[find(i)] = find(j)
        groups = {}
        for i, cell in enumerate(cells):
            groups.setdefault(find(i), []).append(cell)

        # for each instance, find the unique alignment and stamp the template
        for grp in groups.values():
            fr0, fc0 = grp[0]
            for (sdr, sdc) in same:
                tr, tc = fr0 - sdr, fc0 - sdc
                if all((fr - tr, fc - tc) in same_set for (fr, fc) in grp):
                    for dr, dc, v in rel:
                        rr, cc = tr + dr, tc + dc
                        if 0 <= rr < H and 0 <= cc < W:
                            T[(rr, cc)] = v
                    break
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
