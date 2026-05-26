"""Canonical solver for ARC puzzle 22806e14.

Rule
----
The grid has a background color and two non-background colors:
  * a "main" color forming many filled square blocks (sizes 1x1, 2x2, ...),
  * a unique "marker" color that draws a single plus / cross shape (5 cells).

The marker color is the stamp color. For every main-color square block whose
side length is ODD (1, 3, 5, 7, ...), the centre cell of that block is recoloured
to the marker color (even-sided blocks have no single centre and are left alone).

The marker plus itself is erased (set to background) IFF every odd-sided block
has a distinct side length (i.e. the odd sizes are all unique). If two or more
odd blocks share a size, the marker plus is kept in place.
"""

from collections import Counter


def _components(grid, color):
    """4-connected components of cells equal to `color`. Returns list of cell lists."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] != color:
                        continue
                    seen.add((a, b))
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    """Build the latent transformation mask: dict {(r, c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    counts = Counter(v for row in input_grid for v in row)
    bg = counts.most_common(1)[0][0]

    # Non-background colors and their cell counts.
    fg = {v: n for v, n in counts.items() if v != bg}
    if len(fg) < 2:
        return {}

    # Marker color = the unique plus/cross shape (5 cells forming a cross).
    marker = None
    for color in fg:
        for cells in _components(input_grid, color):
            if len(cells) != 5:
                continue
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            if r1 - r0 == 2 and c1 - c0 == 2:
                cr, cc = (r0 + r1) // 2, (c0 + c1) // 2
                cross = {(cr, cc), (cr - 1, cc), (cr + 1, cc),
                         (cr, cc - 1), (cr, cc + 1)}
                if set(cells) == cross:
                    marker = color
                    marker_cells = cells
                    break
        if marker is not None:
            break
    if marker is None:
        return {}

    # Main color = the most populous non-background, non-marker color.
    main_candidates = {v: n for v, n in fg.items() if v != marker}
    if not main_candidates:
        return {}
    main = max(main_candidates, key=main_candidates.get)

    # Collect main-color blocks; record odd-sided square centres.
    odd_sides = []
    centers = []
    for cells in _components(input_grid, main):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        h, w = r1 - r0 + 1, c1 - c0 + 1
        if h == w and len(cells) == h * w and h % 2 == 1:  # filled odd square
            odd_sides.append(h)
            centers.append(((r0 + r1) // 2, (c0 + c1) // 2))

    T = {}
    # Stamp the marker color onto each odd-square centre.
    for (cr, cc) in centers:
        T[(cr, cc)] = marker

    # Erase the marker plus iff all odd-square sizes are distinct.
    if len(odd_sides) == len(set(odd_sides)):
        for (r, c) in marker_cells:
            T[(r, c)] = bg

    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
