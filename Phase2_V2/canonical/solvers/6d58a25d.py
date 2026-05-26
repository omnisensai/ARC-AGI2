def infer_T(input_grid):
    """Infer a latent mask {(r,c): color} of the cells to overwrite.

    Structure: the grid contains one multi-cell 'sprayer' shape (a single
    color forming a connected component) plus scattered single dots of a
    second color. For every dot located BELOW the sprayer and within its
    column span, that dot's column becomes a downward ray of the dot color,
    starting just below the lowest sprayer cell in that column and running
    to the bottom edge.
    """
    from collections import Counter
    H, W = len(input_grid), len(input_grid[0])

    def components(col):
        cells = set((r, c) for r in range(H) for c in range(W) if input_grid[r][c] == col)
        seen, comps = set(), []
        for s in cells:
            if s in seen:
                continue
            stack, comp = [s], []
            while stack:
                r, c = stack.pop()
                if (r, c) in seen or (r, c) not in cells:
                    continue
                seen.add((r, c)); comp.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        stack.append((r + dr, c + dc))
            comps.append(comp)
        return comps

    counts = Counter(v for row in input_grid for v in row if v)
    shape_col = None
    shape_cells = None
    for col in counts:
        big = max(components(col), key=len)
        if len(big) >= 4:
            shape_col = col
            shape_cells = big
            break

    T = {}
    if shape_col is None:
        return T

    dot_col = next((c for c in counts if c != shape_col), None)
    if dot_col is None:
        return T

    cells = set(shape_cells)
    rows = [r for r, c in cells]
    cols = [c for r, c in cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)

    # lowest sprayer-cell row per column
    bottom = {}
    for r, c in cells:
        bottom[c] = max(bottom.get(c, -1), r)

    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == dot_col and r > r1 and c0 <= c <= c1:
                start = bottom[c] + 1
                for rr in range(start, H):
                    T[(rr, c)] = dot_col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
