"""Canonical solver for ARC puzzle 94be5b80.

Rule: the grid contains (a) a "legend": a solid rectangle of K columns, each
column a single distinct color, giving an ordered color sequence
[c0..c_{K-1}]; and (b) one or more copies of a single repeated shape, each copy
in its own color, stacked vertically and identical when normalized to their
bounding-box top-left. The transform removes the legend and rebuilds a vertical
stack of K copies of the shape (same column position, stacked with stride =
shape height), colored by the legend sequence in order, anchored so that an
already-present colored copy stays at its original location.
"""


def _components(g):
    H, W = len(g), len(g[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W) or g[a][b] == 0:
                        continue
                    seen.add((a, b))
                    cells.append((a, b))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((a + dr, b + dc))
                comps.append(cells)
    return comps


def _is_legend(g, cells):
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    h = max(rs) - min(rs) + 1
    w = max(cs) - min(cs) + 1
    if w < 2 or len(cells) != h * w:
        return False  # must be a full filled rectangle wider than 1 column
    by_col = {}
    for r, c in cells:
        by_col.setdefault(c, set()).add(g[r][c])
    if any(len(s) != 1 for s in by_col.values()):
        return False  # each column a single color
    seq = [next(iter(by_col[c])) for c in sorted(by_col)]
    if len(set(seq)) != len(seq):
        return False  # distinct colors across columns
    return True


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    T = {}

    comps = _components(g)
    legend = None
    shape_comps = []
    for cells in comps:
        if legend is None and _is_legend(g, cells):
            legend = cells
        else:
            shape_comps.append(cells)
    if legend is None or not shape_comps:
        return T

    # legend color sequence, left to right
    by_col = {}
    for r, c in legend:
        by_col[c] = g[r][c]
    seq = [by_col[c] for c in sorted(by_col)]

    # split the shape cells by color (each color is one copy of the shape)
    by_color = {}
    for cells in shape_comps:
        for r, c in cells:
            by_color.setdefault(g[r][c], []).append((r, c))

    # unit shape: normalize one copy to its own bbox top-left
    sample_cells = next(iter(by_color.values()))
    s_top = min(r for r, c in sample_cells)
    s_left = min(c for r, c in sample_cells)
    rel = frozenset((r - s_top, c - s_left) for r, c in sample_cells)
    height = max(dr for dr, dc in rel) + 1

    # anchor: a present color that is in the legend fixes the stack position
    anchor = None
    for col, cells in by_color.items():
        if col in seq:
            top = min(r for r, c in cells)
            left = min(c for r, c in cells)
            anchor = (top, left, seq.index(col))
            break
    if anchor is None:
        return T
    top0, left0, k0 = anchor
    base_top = top0 - k0 * height

    # remove the legend
    for r, c in legend:
        T[(r, c)] = 0

    # rebuild the stack in legend order
    for i, col in enumerate(seq):
        t = base_top + i * height
        for dr, dc in rel:
            rr, cc = t + dr, left0 + dc
            if 0 <= rr < H and 0 <= cc < W:
                T[(rr, cc)] = col

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
