def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # collect non-background cells grouped by color
    cells_by_color = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg:
                cells_by_color.setdefault(v, []).append((r, c))

    T = [[None] * W for _ in range(H)]

    for color, cells in cells_by_color.items():
        cellset = set(cells)
        # split into 8-connected components (independent shapes of same color)
        seen = set()
        comps = []
        for start in cells:
            if start in seen:
                continue
            comp = []
            stack = [start]
            while stack:
                cur = stack.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                comp.append(cur)
                r, c = cur
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nb = (r + dr, c + dc)
                        if nb in cellset and nb not in seen:
                            stack.append(nb)
            comps.append(comp)

        # each shape is a funnel: two diagonal arms meeting a solid base.
        # fill horizontally between the leftmost and rightmost cell of the
        # shape on every row it occupies.
        for comp in comps:
            rows = {}
            for (r, c) in comp:
                rows.setdefault(r, []).append(c)
            for r, cs in rows.items():
                lo, hi = min(cs), max(cs)
                for c in range(lo, hi + 1):
                    if input_grid[r][c] == bg:
                        T[r][c] = color
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out
