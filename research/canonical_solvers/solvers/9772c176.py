"""Canonical solver for ARC puzzle 9772c176.

Rule: the input contains octagonal shapes (chamfered-corner blobs) drawn in a
single non-background color. Each octagon has four flat edges (top, bottom,
left, right). For every flat edge, draw an outward-pointing isosceles triangle
of color 4 starting one cell beyond the edge: the first triangle line has width
(flat_edge_length - 2) and each successive line shrinks by 2 (one cell off each
side) until it reaches width 1, the triangle being centered on the edge. The
transformation mask T records exactly which background cells become 4; cells
that fall outside the grid are clipped.
"""


def find_components(g, color):
    H, W = len(g), len(g[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    cr, cc = stack.pop()
                    if (cr, cc) in seen or not (0 <= cr < H and 0 <= cc < W):
                        continue
                    if g[cr][cc] != color:
                        continue
                    seen.add((cr, cc))
                    comp.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((cr + dr, cc + dc))
                comps.append(comp)
    return comps


def _add_triangle(T, start, center, width, step, orient, H, W, fill):
    """Stamp a shrinking outward triangle into mask T.

    start  : the line index (row for 'h', col for 'v') of the first triangle row.
    center : center coordinate of the flat edge (the triangle's axis).
    width  : width of the first triangle line.
    step   : +1 / -1 direction the triangle grows away from the shape.
    orient : 'h' -> lines run horizontally; 'v' -> lines run vertically.
    """
    line = start
    w = width
    while w >= 1:
        half = (w - 1) / 2
        lo = int(center - half)
        hi = int(center + half)
        for k in range(lo, hi + 1):
            if orient == 'h':
                r, c = line, k
            else:
                r, c = k, line
            if 0 <= r < H and 0 <= c < W:
                T[(r, c)] = fill
        line += step
        w -= 2


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    cnt = {}
    for row in input_grid:
        for v in row:
            cnt[v] = cnt.get(v, 0) + 1
    bg = max(cnt, key=cnt.get)
    shape_colors = [v for v in cnt if v != bg]
    fill = 4
    T = {}
    for color in shape_colors:
        for comp in find_components(input_grid, color):
            rs = [r for r, c in comp]
            cs = [c for r, c in comp]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)

            top = [c for (r, c) in comp if r == r0]
            tc0, tc1 = min(top), max(top)
            _add_triangle(T, r0 - 1, (tc0 + tc1) / 2, (tc1 - tc0 + 1) - 2,
                          -1, 'h', H, W, fill)

            bot = [c for (r, c) in comp if r == r1]
            bc0, bc1 = min(bot), max(bot)
            _add_triangle(T, r1 + 1, (bc0 + bc1) / 2, (bc1 - bc0 + 1) - 2,
                          +1, 'h', H, W, fill)

            left = [r for (r, c) in comp if c == c0]
            lr0, lr1 = min(left), max(left)
            _add_triangle(T, c0 - 1, (lr0 + lr1) / 2, (lr1 - lr0 + 1) - 2,
                          -1, 'v', H, W, fill)

            right = [r for (r, c) in comp if c == c1]
            rr0, rr1 = min(right), max(right)
            _add_triangle(T, c1 + 1, (rr0 + rr1) / 2, (rr1 - rr0 + 1) - 2,
                          +1, 'v', H, W, fill)
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
