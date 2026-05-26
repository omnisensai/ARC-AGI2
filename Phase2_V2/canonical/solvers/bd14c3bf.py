"""Canonical solver for ARC puzzle bd14c3bf.

Rule (inferred from input structure alone):
  The grid contains one "template" object drawn in color 2 plus many candidate
  objects drawn in color 1 (background 0). The template encodes a SCALE-FREE
  pattern: run-length compressing it (collapsing consecutive identical rows and
  columns to a single representative) yields a canonical shape. A color-1 object
  is recolored to 2 exactly when its own run-length-compressed shape matches the
  template's compressed shape under one of the 8 dihedral orientations
  (rotations/reflections). I.e. every object that is a stretched copy of the
  template gets repainted with the template's color; all other color-1 objects
  are left untouched.

infer_T computes the latent mask {(r,c): 2} of cells to recolor; apply_T copies
the input and overwrites only those cells.
"""


def _components(grid, color):
    """8-connected components of `color`."""
    H, W = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen:
                        continue
                    if not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if grid[rr][cc] != color:
                        continue
                    seen.add((rr, cc))
                    cells.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((rr + dr, cc + dc))
                out.append(cells)
    return out


def _mat(cells):
    """Boolean occupancy matrix of a component within its bounding box."""
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    s = set(cells)
    return tuple(
        tuple((r, c) in s for c in range(c0, c1 + 1))
        for r in range(r0, r1 + 1)
    )


def _compress(m):
    """Collapse consecutive identical rows then consecutive identical columns."""
    rows = []
    for row in m:
        if not rows or rows[-1] != row:
            rows.append(row)
    m2 = tuple(rows)
    cols = list(zip(*m2))
    cc = []
    for col in cols:
        if not cc or cc[-1] != col:
            cc.append(col)
    return tuple(zip(*cc))


def _rot90(m):
    return tuple(zip(*m[::-1]))


def _flip(m):
    return tuple(row[::-1] for row in m)


def _orientations(m):
    res = set()
    cur = m
    for _ in range(4):
        res.add(cur)
        res.add(_flip(cur))
        cur = _rot90(cur)
    return res


def infer_T(input_grid):
    """Return latent transformation mask: dict {(r, c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])

    # Locate the unique template object (color 2). If absent, no change.
    templates = _components(input_grid, 2)
    T = {}
    if not templates:
        return T

    # Build the scale-free signature of the template (all 8 orientations).
    tmpl_sig = _orientations(_compress(_mat(templates[0])))

    # Each color-1 object that, after run-length compression, matches the
    # template signature is a stretched copy -> recolor its cells to 2.
    for comp in _components(input_grid, 1):
        sig = _compress(_mat(comp))
        if sig in tmpl_sig:
            for (r, c) in comp:
                T[(r, c)] = 2
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
