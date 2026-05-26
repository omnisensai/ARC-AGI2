"""Canonical ARC solver for puzzle f21745ec.

Rule:
  The grid contains several rectangular "boxes" (one solid-color border each).
  Exactly one box is a TEMPLATE: its interior holds a pattern of non-background
  cells. Every empty box whose interior dimensions equal the template's interior
  dimensions is filled with the template pattern (painted in its own border
  color). Empty boxes whose interior size differs from the template are erased.

Canonical latent-T form: infer_T builds a {(r,c): new_color} mask from input
structure alone; apply_T copies the input and overwrites only masked cells.
"""


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _find_objects(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    if cr < 0 or cr >= H or cc < 0 or cc >= W:
                        continue
                    if seen[cr][cc] or grid[cr][cc] != color:
                        continue
                    seen[cr][cc] = True
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((cr + dr, cc + dc))
                objs.append((color, cells))
    return objs


def _bbox(cells):
    rs = [c[0] for c in cells]
    cs = [c[1] for c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def infer_T(input_grid):
    """Return a latent mask dict {(r,c): new_color} of cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    objs = _find_objects(input_grid, bg)

    boxes = []  # (color, r0, c0, r1, c1, interior_pattern, has_pattern)
    for color, cells in objs:
        r0, c0, r1, c1 = _bbox(cells)
        # interior binary pattern (1 = non-background)
        pat = [[1 if input_grid[r][c] != bg else 0 for c in range(c0 + 1, c1)]
               for r in range(r0 + 1, r1)]
        has_pat = any(any(row) for row in pat)
        boxes.append((color, r0, c0, r1, c1, pat, has_pat))

    # The template is the unique box with a non-empty interior pattern.
    template = next((b for b in boxes if b[6]), None)
    if template is None:
        return {}

    _, tr0, tc0, tr1, tc1, tpat, _ = template
    tih, tiw = tr1 - tr0 - 1, tc1 - tc0 - 1  # interior height/width

    T = {}
    for color, r0, c0, r1, c1, pat, has_pat in boxes:
        if has_pat:
            continue  # template stays as-is
        ih, iw = r1 - r0 - 1, c1 - c0 - 1
        if ih == tih and iw == tiw:
            # fill interior with the template pattern in this box's color
            for dr in range(ih):
                for dc in range(iw):
                    if tpat[dr][dc]:
                        T[(r0 + 1 + dr, c0 + 1 + dc)] = color
        else:
            # erase the whole box (border + interior) to background
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if input_grid[r][c] == color:
                        T[(r, c)] = bg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
