"""Canonical solver for ARC puzzle 9b2a60aa.

Rule
----
The grid contains one small multi-cell TEMPLATE shape (a single color) plus a
line of isolated single-cell MARKERS (all sharing one row or one column). One
marker has the same color as the template -- that is the KEY marker, and the
template is the template's stamp for that marker (it stays put).

For every other marker, a recolored copy of the template is stamped along the
marker line. Walking outward from the key marker, each successive stamp is
offset from the previous stamp, along the marker axis, by
    (gap between the two markers) + (template size along that axis - 1).
The perpendicular position of every stamp equals the template's perpendicular
position. Each stamp is painted in its marker's color.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # 8-connected components of non-zero cells.
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                seen[r][c] = True
                while stack:
                    y, x = stack.pop()
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        ny, nx = y + dy, x + dx
                        if (0 <= ny < H and 0 <= nx < W and not seen[ny][nx]
                                and input_grid[ny][nx] != 0):
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                comps.append(cells)

    # Template: the multi-cell component. Markers: isolated single cells.
    template_cells = max(comps, key=len)
    tcolor = input_grid[template_cells[0][0]][template_cells[0][1]]
    tr0 = min(y for y, x in template_cells)
    tr1 = max(y for y, x in template_cells)
    tc0 = min(x for y, x in template_cells)
    tc1 = max(x for y, x in template_cells)
    th = tr1 - tr0 + 1
    tw = tc1 - tc0 + 1
    rel = [(y - tr0, x - tc0) for y, x in template_cells]

    markers = [cells[0] for cells in comps if len(cells) == 1]

    # Marker axis: shared column -> stamps progress along rows (vertical),
    # otherwise shared row -> stamps progress along columns.
    cols = set(x for y, x in markers)
    vertical = len(cols) == 1

    T = {}
    if vertical:
        markers_sorted = sorted(markers, key=lambda m: m[0])
        key_idx = next(i for i, m in enumerate(markers_sorted)
                       if input_grid[m[0]][m[1]] == tcolor)
        n = len(markers_sorted)
        tops = [None] * n
        tops[key_idx] = tr0
        for i in range(key_idx + 1, n):
            gap = markers_sorted[i][0] - markers_sorted[i - 1][0]
            tops[i] = tops[i - 1] + gap + (th - 1)
        for i in range(key_idx - 1, -1, -1):
            gap = markers_sorted[i + 1][0] - markers_sorted[i][0]
            tops[i] = tops[i + 1] - (gap + (th - 1))
        for i, m in enumerate(markers_sorted):
            if i == key_idx:
                continue
            color = input_grid[m[0]][m[1]]
            top = tops[i]
            for dy, dx in rel:
                T[(top + dy, tc0 + dx)] = color
    else:
        markers_sorted = sorted(markers, key=lambda m: m[1])
        key_idx = next(i for i, m in enumerate(markers_sorted)
                       if input_grid[m[0]][m[1]] == tcolor)
        n = len(markers_sorted)
        lefts = [None] * n
        lefts[key_idx] = tc0
        for i in range(key_idx + 1, n):
            gap = markers_sorted[i][1] - markers_sorted[i - 1][1]
            lefts[i] = lefts[i - 1] + gap + (tw - 1)
        for i in range(key_idx - 1, -1, -1):
            gap = markers_sorted[i + 1][1] - markers_sorted[i][1]
            lefts[i] = lefts[i + 1] - (gap + (tw - 1))
        for i, m in enumerate(markers_sorted):
            if i == key_idx:
                continue
            color = input_grid[m[0]][m[1]]
            left = lefts[i]
            for dy, dx in rel:
                T[(tr0 + dy, left + dx)] = color
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
