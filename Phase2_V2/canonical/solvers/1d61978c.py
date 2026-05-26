"""Canonical solver for ARC puzzle 1d61978c.

Rule
----
The grid contains a set of color-5 cells that form straight diagonal
segments. Every connected diagonal segment lies entirely along one of the
two diagonal slopes:

    "\\"  (down-right: column increases as row increases)
    "/"   (down-left:  column decreases as row increases)

All cells of one slope are recolored 8, and all cells of the other slope
are recolored 2. The slope that covers MORE cells (the majority slope)
becomes 8; the minority slope becomes 2. Every other cell is left as-is.

Canonical latent-T form: ``infer_T`` builds a {(r,c): new_color} mask from
the input structure alone; ``apply_T`` copies the input and overwrites only
the masked cells.
"""


def _diagonal_components(grid):
    """Connected components of color-5 cells using diagonal adjacency."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 5 and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    x, y = stack.pop()
                    if (x, y) in seen:
                        continue
                    if not (0 <= x < H and 0 <= y < W) or grid[x][y] != 5:
                        continue
                    seen.add((x, y))
                    comp.append((x, y))
                    for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((x + dr, y + dc))
                comps.append(comp)
    return comps


def _slope(comp):
    """Return '\\' or '/' for a diagonal segment."""
    pts = sorted(comp)
    (r0, c0), (r1, c1) = pts[0], pts[-1]
    if r1 == r0:
        return '\\'  # single cell; orientation irrelevant for coloring
    return '\\' if (c1 - c0) > 0 else '/'


def infer_T(input_grid):
    """Infer the recolor mask {(r,c): new_color} from input structure alone."""
    comps = _diagonal_components(input_grid)

    # Tally how many color-5 cells belong to each slope.
    cells = {'\\': 0, '/': 0}
    comp_slopes = []
    for comp in comps:
        sl = _slope(comp)
        comp_slopes.append((comp, sl))
        cells[sl] += len(comp)

    # Majority slope -> 8, minority slope -> 2.
    if cells['\\'] >= cells['/']:
        color = {'\\': 8, '/': 2}
    else:
        color = {'\\': 2, '/': 8}

    T = {}
    for comp, sl in comp_slopes:
        new_color = color[sl]
        for (r, c) in comp:
            T[(r, c)] = new_color
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the cells named in the mask."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
