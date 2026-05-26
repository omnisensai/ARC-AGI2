"""Canonical latent-T solver for ARC puzzle f8be4b64.

Structure of every input: a background of 0s containing several "plus" markers.
A plus is a center cell whose four orthogonal neighbours are all color 3.
  - A *colored* plus has a center color c in {1..9}\\{3}.
  - An *empty* plus has center color 0.

Each colored plus shoots four rays (up/down/left/right) of its own color from
its center.  A ray travels cell by cell, painting background cells with the
plus color, skipping over its own plus's cells (the 3 arms / center), and
stopping the instant it would enter a cell belonging to ANOTHER plus.

Empty pluses shoot rays of color 0 (transparent barriers) the same way.

When two rays cross, the VERTICAL ray always paints over the horizontal one.
Hence an empty plus's vertical ray punches 0-gaps through any horizontal
colored ray it crosses, while its horizontal 0-ray is invisible.

infer_T builds the latent mask {(r,c): new_color} purely from this geometry;
apply_T copies the input and overwrites only the masked cells.
"""

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _find_pluses(g):
    """Return list of (r, c, center_color) for every plus marker."""
    H, W = len(g), len(g[0])
    pluses = []
    for r in range(1, H - 1):
        for c in range(1, W - 1):
            if (g[r - 1][c] == 3 and g[r + 1][c] == 3 and
                    g[r][c - 1] == 3 and g[r][c + 1] == 3):
                pluses.append((r, c, g[r][c]))
    return pluses


def _plus_cells(pluses):
    """Map every cell occupied by a plus (center + 4 arms) to its plus index."""
    owner = {}
    for i, (r, c, _col) in enumerate(pluses):
        owner[(r, c)] = i
        for dr, dc in DIRS:
            owner[(r + dr, c + dc)] = i
    return owner


def _cast_ray(g, owner, idx, r, c, dr, dc):
    """Cast one ray from center (r,c) in direction (dr,dc).

    Yields the background cells the ray paints.  Skips over the ray's own plus
    cells; stops when it reaches a cell owned by a different plus or the edge.
    """
    H, W = len(g), len(g[0])
    nr, nc = r + dr, c + dc
    cells = []
    while 0 <= nr < H and 0 <= nc < W:
        own = owner.get((nr, nc))
        if own is not None:
            if own == idx:          # our own arm -> pass straight through
                nr += dr
                nc += dc
                continue
            break                   # another plus -> ray stops here
        cells.append((nr, nc))      # background -> paint it
        nr += dr
        nc += dc
    return cells


def infer_T(input_grid):
    """Infer the latent transformation mask as {(r, c): new_color}."""
    g = input_grid
    pluses = _find_pluses(g)
    owner = _plus_cells(pluses)

    horizontal = {}   # (r,c) -> color  (left/right rays)
    vertical = {}     # (r,c) -> color  (up/down rays); wins over horizontal

    for idx, (r, c, col) in enumerate(pluses):
        for dr, dc in DIRS:
            cells = _cast_ray(g, owner, idx, r, c, dr, dc)
            target = vertical if dr != 0 else horizontal
            for (rr, cc) in cells:
                target[(rr, cc)] = col

    T = {}
    # horizontal rays first, vertical rays overwrite them.
    for cell, col in horizontal.items():
        T[cell] = col
    for cell, col in vertical.items():
        T[cell] = col
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
