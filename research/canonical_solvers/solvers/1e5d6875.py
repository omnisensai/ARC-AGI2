"""Canonical solver for ARC puzzle 1e5d6875.

Rule:
  The grid contains L-trominoes (a 2x2 box with one corner missing) on a
  background of 7. Each L has a "corner" cell (the cell diagonally opposite the
  missing corner) which defines a diagonal direction (corner -> missing corner).
  For every L of color 5 we stamp a translated copy of it in color 4, shifted by
  one step along that diagonal direction. For every L of color 2 we stamp a
  translated copy in color 3, shifted by one step along the OPPOSITE diagonal
  direction. Stamped cells are written only onto background cells (clipped at the
  grid border and never overwriting existing shapes).
"""


def _components(grid, color):
    """8-connected components of `color` in `grid`."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    x, y = stack.pop()
                    if (x, y) in seen or not (0 <= x < H and 0 <= y < W):
                        continue
                    if grid[x][y] != color:
                        continue
                    seen.add((x, y))
                    cells.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((x + dx, y + dy))
                comps.append(cells)
    return comps


def _l_geometry(cells):
    """Given an L-tromino, return (missing_corner, full_corner)."""
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    box = [(r, c) for r in (r0, r1) for c in (c0, c1)]
    cellset = set(cells)
    missing = next(p for p in box if p not in cellset)
    corner = (r0 + r1 - missing[0], c0 + c1 - missing[1])
    return missing, corner


def infer_T(input_grid):
    """Compute the latent transformation mask {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    bg = 7
    T = {}
    # color 5 -> 4 stamped along corner->missing direction;
    # color 2 -> 3 stamped along the opposite direction.
    for color, new_color, sign in ((5, 4, 1), (2, 3, -1)):
        for cells in _components(input_grid, color):
            if len(cells) != 3:
                continue  # only well-formed L-trominoes
            missing, corner = _l_geometry(cells)
            dr = (missing[0] - corner[0]) * sign
            dc = (missing[1] - corner[1]) * sign
            for (r, c) in cells:
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W and input_grid[nr][nc] == bg:
                    T[(nr, nc)] = new_color
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
