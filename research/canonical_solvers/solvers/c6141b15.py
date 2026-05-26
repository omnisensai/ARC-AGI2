"""Canonical solver for ARC puzzle c6141b15.

Rule (inferred from all train/test pairs):
  The grid contains two non-background objects of different colors:
    * a "bar": a single straight-line connected component (color appears as
      exactly one component);
    * "markers": several identical small shapes (the other color appears as
      >= 2 components, all sharing one normalized shape).
  The transformation swaps the two roles geometrically:
    * marker shapes are stamped (in the marker color) centered on each of the
      two endpoints of the bar;
    * the bar color is redrawn as the closed polygon connecting every pair of
      marker centers (straight horizontal / vertical / 45-degree segments).
  All original object cells are cleared back to background.

Canonical latent-T form: infer_T builds a {(r,c): new_color} mask of every
cell that must change; apply_T copies the input and overwrites only those.
"""


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if (y, x) in seen or not (0 <= y < H and 0 <= x < W):
                        continue
                    if grid[y][x] != color:
                        continue
                    seen.add((y, x))
                    cells.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy or dx:
                                stack.append((y + dy, x + dx))
                comps.append(sorted(cells))
    return comps


def _bbox_center(cells):
    ys = [y for y, x in cells]
    xs = [x for y, x in cells]
    return ((min(ys) + max(ys)) / 2.0, (min(xs) + max(xs)) / 2.0)


def _line_endpoints(cells):
    """Return the two extreme cells of a straight-line component."""
    ys = [y for y, x in cells]
    xs = [x for y, x in cells]
    miny, maxy = min(ys), max(ys)
    minx, maxx = min(xs), max(xs)
    if maxy - miny >= maxx - minx:
        # mostly vertical / diagonal sorted by row
        top = min(cells, key=lambda p: (p[0], p[1]))
        bot = max(cells, key=lambda p: (p[0], p[1]))
        return top, bot
    else:
        left = min(cells, key=lambda p: (p[1], p[0]))
        right = max(cells, key=lambda p: (p[1], p[0]))
        return left, right


def _draw_segment(p0, p1):
    """All integer cells of the straight segment p0->p1 (8-direction line)."""
    (r0, c0), (r1, c1) = p0, p1
    dr = r1 - r0
    dc = c1 - c0
    steps = max(abs(dr), abs(dc))
    cells = []
    if steps == 0:
        return [(r0, c0)]
    sr = dr / steps
    sc = dc / steps
    for i in range(steps + 1):
        cells.append((int(round(r0 + sr * i)), int(round(c0 + sc * i))))
    return cells


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    colors = []
    for row in input_grid:
        for v in row:
            if v != bg and v not in colors:
                colors.append(v)

    # Identify bar (single component) vs markers (multiple components).
    by_color = {col: _components(input_grid, col) for col in colors}
    bar_color = None
    marker_color = None
    for col, comps in by_color.items():
        if len(comps) == 1:
            bar_color = col
        else:
            marker_color = col
    if bar_color is None or marker_color is None:
        # Fallback: the color with fewest components is the bar.
        ordered = sorted(by_color.items(), key=lambda kv: len(kv[1]))
        bar_color = ordered[0][0]
        marker_color = ordered[-1][0]

    bar_cells = by_color[bar_color][0]
    marker_comps = by_color[marker_color]

    # Normalized marker shape (offsets from bbox center) and its cells.
    sample = marker_comps[0]
    cy, cx = _bbox_center(sample)
    shape_offsets = [(y - cy, x - cx) for y, x in sample]

    # Marker centers (in input) -> become polygon vertices.
    centers = [_bbox_center(c) for c in marker_comps]

    # Bar endpoints -> become marker stamp locations.
    ep0, ep1 = _line_endpoints(bar_cells)

    T = {}
    # Clear all original object cells back to background.
    for col in colors:
        for comp in by_color[col]:
            for (r, c) in comp:
                T[(r, c)] = bg

    # Stamp markers at each bar endpoint.
    for (er, ec) in (ep0, ep1):
        for (oy, ox) in shape_offsets:
            r = int(round(er + oy))
            c = int(round(ec + ox))
            if 0 <= r < H and 0 <= c < W:
                T[(r, c)] = marker_color

    # Draw the bar color as the closed polygon over every pair of centers.
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            p0 = (int(round(centers[i][0])), int(round(centers[i][1])))
            p1 = (int(round(centers[j][0])), int(round(centers[j][1])))
            for (r, c) in _draw_segment(p0, p1):
                if 0 <= r < H and 0 <= c < W:
                    T[(r, c)] = bar_color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
