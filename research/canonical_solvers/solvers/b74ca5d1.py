"""Canonical latent-T solver for ARC puzzle b74ca5d1.

Rule (inferred from input structure alone):
  * The background is the most common color. Each non-background corner cell is a
    "marker" carrying a color.
  * Every other non-background color is the "main" color of one shape. Each shape
    occupies a small (5x5) region and contains exactly one foreign "seed" cell whose
    color equals one of the corner-marker colors.
  * In-place transform: inside each shape the main color and its seed color are
    swapped (all main cells -> seed color, the single seed cell -> main color).
  * Corner transform: for each marker color we overlay (union) the masks of all
    shapes whose seed equals that color and draw the union, in the marker color,
    anchored into the corner that carries that marker. When two or more shapes are
    overlaid, a thin 1-wide straight protrusion ("stem") of a shape is dropped if it
    does not touch any cell belonging to another shape in the union.

infer_T builds a latent transformation mask {(r,c): new_color}; apply_T copies the
input and overwrites only the masked cells.
"""

from collections import Counter

N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _background(grid):
    cnt = Counter(v for row in grid for v in row)
    return cnt.most_common(1)[0][0]


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
    """Return list of shapes; each = (maincolor, set(main cells), seedpos, seedcolor)."""
    H, W = len(grid), len(grid[0])
    allcols = set(v for row in grid for v in row) - {bg}
    maincols = sorted(allcols - set(markercols))
    shapes = []
    for mc in maincols:
        cells = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == mc]
        if not cells:
            continue
        ys = [y for y, x in cells]
        xs = [x for y, x in cells]
        r0, r1, c0, c1 = min(ys), max(ys), min(xs), max(xs)
        seedpos = None
        seedcol = None
        for r in range(max(0, r0 - 1), min(H, r1 + 2)):
            for c in range(max(0, c0 - 1), min(W, c1 + 2)):
                if grid[r][c] in markercols:
                    seedpos = (r, c)
                    seedcol = grid[r][c]
        shapes.append((mc, set(cells), seedpos, seedcol))
    return shapes


def _rel_mask(cells, seedpos):
    """Relative mask (anchored to top-left of cells+seed) and its bounding size."""
    pts = set(cells)
    if seedpos is not None:
        pts.add(seedpos)
    ys = [y for y, x in pts]
    xs = [x for y, x in pts]
    r0, c0 = min(ys), min(xs)
    rel = frozenset((y - r0, x - c0) for y, x in pts)
    h = max(ys) - r0
    w = max(xs) - c0
    return rel, h, w


def _stem_cells(mask):
    """Cells belonging to maximal 1-wide straight protrusions ending in a free tip."""
    mset = set(mask)
    stems = set()
    for c in mset:
        nb = [(c[0] + dr, c[1] + dc) for dr, dc in N8 if (c[0] + dr, c[1] + dc) in mset]
        if len(nb) != 1:
            continue
        d = (nb[0][0] - c[0], nb[0][1] - c[1])
        if d not in N4:
            continue
        # walk straight from the tip toward the body
        run = [c]
        prev = c
        cur = nb[0]
        while True:
            run.append(cur)
            others = [(cur[0] + ddr, cur[1] + ddc) for ddr, ddc in N8
                      if (cur[0] + ddr, cur[1] + ddc) in mset and (cur[0] + ddr, cur[1] + ddc) != prev]
            nxt = (cur[0] + d[0], cur[1] + d[1])
            if others == [nxt]:
                prev, cur = cur, nxt
            else:
                run.pop()  # cur is a junction (body), not part of the stem
                break
        stems.update(run)
    return stems


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    markercols = _markers(input_grid, bg)
    shapes = _shapes(input_grid, bg, markercols)

    T = {}

    # 1) In-place swap of main color and seed color for each shape.
    for mc, cells, seedpos, seedcol in shapes:
        if seedcol is None:
            continue
        for (r, c) in cells:
            T[(r, c)] = seedcol
        if seedpos is not None:
            T[seedpos] = mc

    # 2) Corner copies: union of same-seed shapes, anchored into the marker's corner.
    by_seed = {}
    for mc, cells, seedpos, seedcol in shapes:
        if seedcol is None:
            continue
        by_seed.setdefault(seedcol, []).append((cells, seedpos))

    for col, positions in markercols.items():
        group = by_seed.get(col, [])
        if not group:
            continue
        rel_masks = []
        maxh = maxw = 0
        for cells, seedpos in group:
            rel, h, w = _rel_mask(cells, seedpos)
            rel_masks.append(rel)
            maxh = max(maxh, h)
            maxw = max(maxw, w)

        result = set()
        multi = len(rel_masks) > 1
        for i, rel in enumerate(rel_masks):
            keep = set(rel)
            if multi:
                others = set()
                for j, other in enumerate(rel_masks):
                    if j != i:
                        others |= other
                stems = _stem_cells(rel)
                if stems and not (stems & others):
                    keep -= stems
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
