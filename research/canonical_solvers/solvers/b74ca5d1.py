"""Canonical latent-T solver for ARC puzzle b74ca5d1.

Structure of every input
-------------------------
* The background is the single most common color.
* Each non-background corner cell of the grid is a "marker" carrying a color.
* Every remaining non-background color is the "main" color of exactly one small
  (<=5x5) shape.  Each shape contains exactly one foreign "seed" cell whose color
  equals one of the corner-marker colors; the seed tells the shape which corner it
  belongs to.

Transformation (the latent T)
-----------------------------
1. In-place recolor: inside every shape the main color and the seed color are
   swapped -- all main-color cells take the seed color, and the single seed cell
   takes the shape's main color.
2. Corner stamps: for each marker color we overlay (set-union) the cell masks of
   all shapes whose seed equals that color, and draw that union -- in the marker
   color -- anchored into the corner(s) carrying that marker.  Where two or more
   shapes are stamped together, a 1-wide straight protrusion of a shape that does
   not touch any other stamped shape is treated as a connector and is not drawn.

infer_T returns the latent mask as a dict {(r,c): new_color}; apply_T copies the
input and overwrites only the masked cells.
"""

from collections import Counter

N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def _background(grid):
    return Counter(v for row in grid for v in row).most_common(1)[0][0]


def _markers(grid, bg):
    H, W = len(grid), len(grid[0])
    corners = [(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]
    mk = {}
    for (r, c) in corners:
        v = grid[r][c]
        if v != bg:
            mk.setdefault(v, []).append((r, c))
    return mk


def _shapes(grid, bg, markercols):
    """Return [(maincolor, set(main cells), seedpos, seedcolor), ...]."""
    H, W = len(grid), len(grid[0])
    maincols = sorted(set(v for row in grid for v in row) - {bg} - set(markercols))
    shapes = []
    for mc in maincols:
        cells = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == mc]
        if not cells:
            continue
        ys = [y for y, x in cells]
        xs = [x for y, x in cells]
        r0, r1, c0, c1 = min(ys), max(ys), min(xs), max(xs)
        seedpos = seedcol = None
        for r in range(max(0, r0 - 1), min(H, r1 + 2)):
            for c in range(max(0, c0 - 1), min(W, c1 + 2)):
                if grid[r][c] in markercols:
                    seedpos, seedcol = (r, c), grid[r][c]
        shapes.append((mc, set(cells), seedpos, seedcol))
    return shapes


def _rel_mask(cells, seedpos):
    pts = set(cells)
    if seedpos is not None:
        pts.add(seedpos)
    ys = [y for y, x in pts]
    xs = [x for y, x in pts]
    r0, c0 = min(ys), min(xs)
    return frozenset((y - r0, x - c0) for y, x in pts), max(ys) - r0, max(xs) - c0


def _deg(c, mset, nbrs):
    return sum(1 for dr, dc in nbrs if (c[0] + dr, c[1] + dc) in mset)


def _stems(mask):
    """Cells of 1-wide straight orthogonal protrusions that hang off a body.

    A stem is a straight horizontal/vertical run that starts at a free tip (a cell
    with a single 8-neighbour) and terminates at an orthogonal junction (a cell with
    >=3 orthogonal neighbours).  Pure straight lines with no junction are NOT stems
    (they are bodies), and purely diagonal structures (diamonds) are never touched.
    """
    mset = set(mask)
    stems = set()
    for c in mset:
        if _deg(c, mset, N8) != 1:
            continue
        d = None
        for dr, dc in N4:
            if (c[0] + dr, c[1] + dc) in mset:
                d = (dr, dc)
        if d is None:
            continue
        run = [c]
        cur = (c[0] + d[0], c[1] + d[1])
        while True:
            if _deg(cur, mset, N4) >= 3:
                stems.update(run)
                break
            nxt = (cur[0] + d[0], cur[1] + d[1])
            if _deg(cur, mset, N4) == 2 and nxt in mset:
                run.append(cur)
                cur = nxt
            else:
                break
    return stems


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    markercols = _markers(input_grid, bg)
    shapes = _shapes(input_grid, bg, markercols)

    T = {}

    # 1) In-place swap of main color and seed color.
    for mc, cells, seedpos, seedcol in shapes:
        if seedcol is None:
            continue
        for (r, c) in cells:
            T[(r, c)] = seedcol
        if seedpos is not None:
            T[seedpos] = mc

    # 2) Corner stamps.
    by_seed = {}
    for mc, cells, seedpos, seedcol in shapes:
        if seedcol is None:
            continue
        rel, h, w = _rel_mask(cells, seedpos)
        by_seed.setdefault(seedcol, []).append((rel, h, w))

    for col, positions in markercols.items():
        group = by_seed.get(col, [])
        if not group:
            continue
        rel_masks = [g[0] for g in group]
        maxh = max(g[1] for g in group)
        maxw = max(g[2] for g in group)

        result = set()
        multi = len(rel_masks) > 1
        for i, rel in enumerate(rel_masks):
            keep = set(rel)
            if multi:
                others = set()
                for j, other in enumerate(rel_masks):
                    if j != i:
                        others |= other
                st = _stems(rel)
                if st and not (st & others):
                    keep -= st
            result |= keep

        for (cr, cc) in positions:
            ar = 0 if cr == 0 else H - 1 - maxh
            ac = 0 if cc == 0 else W - 1 - maxw
            for (dr, dc) in result:
                rr, ccc = ar + dr, ac + dc
                if 0 <= rr < H and 0 <= ccc < W:
                    T[(rr, ccc)] = col

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
