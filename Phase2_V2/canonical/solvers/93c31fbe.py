"""Canonical solver for ARC puzzle 93c31fbe.

Rule
----
The grid contains rectangular "boxes" whose four corners are marked by 3-cell
L-shaped brackets (a 2x2 minus one cell) drawn in a single non-background,
non-1 color. Inside each box are some color-1 cells. Stray color-1 fragments
also lie outside the boxes.

The transformation:
  - Removes every stray color-1 cell that is NOT inside a box interior.
  - For each box, makes its interior color-1 content mirror-symmetric:
      * if the box is wider than tall, reflect the interior 1s left-right
        about the vertical center line;
      * if the box is taller than wide, reflect them top-bottom about the
        horizontal center line;
      * (a square box would do both).

The latent transformation T is a dict {(r,c): new_color}; apply_T copies the
input and overwrites only the masked cells.
"""


def _components(g, color):
    H, W = len(g), len(g[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if (y, x) in seen or not (0 <= y < H and 0 <= x < W):
                        continue
                    if g[y][x] != color:
                        continue
                    seen.add((y, x))
                    cells.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy or dx:
                                stack.append((y + dy, x + dx))
                out.append(cells)
    return out


def _bracket_corner(cells):
    """Corner cell of a 3-cell L bracket: the cell opposite the missing 2x2 cell."""
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    full = {(r, c) for r in (r0, r1) for c in (c0, c1)}
    missing = list(full - set(cells))[0]
    mr, mc = missing
    cr = r1 if mr == r0 else r0
    cc = c1 if mc == c0 else c0
    return (cr, cc)


def _find_box_rects(g, boxc):
    """Group bracket corners into box rectangles (r0, c0, r1, c1)."""
    corners = [_bracket_corner(c) for c in _components(g, boxc) if len(c) == 3]
    cset = set(corners)
    boxes = []
    used = set()
    for (r0, c0) in sorted(corners):
        if (r0, c0) in used:
            continue
        cand = [(r1, c1) for (r1, c1) in corners
                if r1 > r0 and c1 > c0 and (r0, c1) in cset and (r1, c0) in cset]
        if cand:
            r1, c1 = min(cand)
            boxes.append((r0, c0, r1, c1))
            for cc in [(r0, c0), (r0, c1), (r1, c0), (r1, c1)]:
                used.add(cc)
    return boxes


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    counts = {}
    for row in g:
        for v in row:
            if v not in (0, 1):
                counts[v] = counts.get(v, 0) + 1
    T = {}
    if not counts:
        return T
    boxc = max(counts, key=counts.get)
    boxes = _find_box_rects(g, boxc)

    # Remove every color-1 cell (strays cleared; in-box ones restored below).
    for r in range(H):
        for c in range(W):
            if g[r][c] == 1:
                T[(r, c)] = 0

    # For each box, restore and mirror its interior 1s.
    for (r0, c0, r1, c1) in boxes:
        h = r1 - r0
        w = c1 - c0
        ins = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)
               if g[r][c] == 1]
        res = set(ins)
        if w >= h:
            for (r, c) in ins:
                res.add((r, c0 + c1 - c))
        if h >= w:
            for (r, c) in ins:
                res.add((r0 + r1 - r, c))
        for (r, c) in res:
            T[(r, c)] = 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
