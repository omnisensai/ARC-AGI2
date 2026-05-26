from collections import Counter


def _components(grid, bg):
    """8-connected same-color components of all non-background cells."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and (r, c) not in seen:
                col = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if (y, x) in seen:
                        continue
                    if not (0 <= y < H and 0 <= x < W):
                        continue
                    if grid[y][x] != col:
                        continue
                    seen.add((y, x))
                    cells.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy or dx:
                                stack.append((y + dy, x + dx))
                comps.append((col, cells))
    return comps


def _is_box(cells):
    """Return (r0,c0,h,w) if the component is a hollow rectangle (perimeter
    fully filled, interior empty), else None."""
    rs = [y for y, x in cells]
    cs = [x for y, x in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    h, w = r1 - r0 + 1, c1 - c0 + 1
    if h < 4 or w < 4:
        return None
    cellset = set(cells)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            onperim = (r == r0 or r == r1 or c == c0 or c == c1)
            if onperim and (r, c) not in cellset:
                return None
            if not onperim and (r, c) in cellset:
                return None
    return (r0, c0, h, w)


def infer_T(input_grid):
    """Latent mask. Background = most common color. Components split into
    hollow-rectangle 'boxes' and scattered 'markers'. The mask erases every
    marker (back to bg), and for each box draws, on its middle interior row,
    a right-aligned line of N dots (spaced every 2 columns) where N is the
    number of marker components sharing the box's color."""
    bg = Counter(v for row in input_grid for v in row).most_common(1)[0][0]
    comps = _components(input_grid, bg)

    boxes = []
    markers = []
    for col, cells in comps:
        bb = _is_box(cells)
        if bb is not None:
            r0, c0, h, w = bb
            boxes.append((col, r0, c0, h, w))
        else:
            markers.append((col, cells))

    marker_count = Counter(col for col, _ in markers)

    T = {}
    # erase all marker cells
    for col, cells in markers:
        for (r, c) in cells:
            T[(r, c)] = bg

    # draw dot lines inside each box
    for (col, r0, c0, h, w) in boxes:
        n = marker_count.get(col, 0)
        if n <= 0:
            continue
        mid_row = r0 + h // 2
        last_col = c0 + w - 3            # rightmost dot = interior right col - 1
        for k in range(n):
            c = last_col - 2 * k
            if c >= c0 + 1:
                T[(mid_row, c)] = col
    return T, bg


def apply_T(input_grid, T):
    mask, bg = T
    out = [row[:] for row in input_grid]
    for (r, c), v in mask.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
