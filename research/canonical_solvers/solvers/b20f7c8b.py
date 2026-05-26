"""Canonical solver for ARC puzzle b20f7c8b.

Structure of every grid:
  * A 6-wide "legend" band whose background is color 8. It holds several
    small glyphs, each drawn in a distinct color: glyph_color -> glyph_shape.
  * The rest of the grid (background 0) holds 5x5 panels. Each panel is one
    of two kinds:
      - "pattern" panel: a color-2 border framing an inner 3x3 made of 1s.
      - "solid" panel: a uniform block of some color (the border color).

Transformation (legend is never touched):
  * pattern panel -> its inner 1-glyph matches exactly one legend glyph under
    dihedral symmetry; fill the whole panel solid with that legend's color.
  * solid panel -> its color is a legend color; redraw it as a color-2 border
    with the legend glyph (exact legend orientation) drawn in 1s inside.
"""


def _legend_band(g):
    H, W = len(g), len(g[0])
    cols = sorted(set(c for r in range(H) for c in range(W) if g[r][c] == 8))
    if not cols:
        return None
    return cols[0], cols[-1] + 1


def _legend_shapes(g, c0, c1):
    """Return dict color -> frozenset(normalized cells) for each legend glyph."""
    H = len(g)
    seen = set()
    out = {}
    for r in range(H):
        for c in range(c0, c1):
            if g[r][c] != 8 and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen:
                        continue
                    if not (0 <= rr < H and c0 <= cc < c1):
                        continue
                    if g[rr][cc] == 8:
                        continue
                    seen.add((rr, cc))
                    cells.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((rr + dr, cc + dc))
                color = g[cells[0][0]][cells[0][1]]
                mr = min(x for x, y in cells)
                mc = min(y for x, y in cells)
                out[color] = frozenset((x - mr, y - mc) for x, y in cells)
    return out


def _find_panels(g, c0, c1):
    """Return list of (r0, c0) top-left corners of each 5x5 panel (0-bg region)."""
    H, W = len(g), len(g[0])
    seen = set()
    panels = []
    for r in range(H):
        for c in range(W):
            if c0 <= c < c1:
                continue
            if g[r][c] != 0 and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen:
                        continue
                    if not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if c0 <= cc < c1:
                        continue
                    if g[rr][cc] == 0:
                        continue
                    seen.add((rr, cc))
                    cells.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((rr + dr, cc + dc))
                minr = min(x for x, y in cells)
                minc = min(y for x, y in cells)
                panels.append((minr, minc))
    return panels


def _normalize(cells):
    if not cells:
        return frozenset()
    mr = min(x for x, y in cells)
    mc = min(y for x, y in cells)
    return frozenset((x - mr, y - mc) for x, y in cells)


def _symmetries(cells):
    cs = list(cells)
    transforms = (
        lambda x, y: (x, y),
        lambda x, y: (-x, y),
        lambda x, y: (x, -y),
        lambda x, y: (-x, -y),
        lambda x, y: (y, x),
        lambda x, y: (-y, x),
        lambda x, y: (y, -x),
        lambda x, y: (-y, -x),
    )
    return set(_normalize([fn(x, y) for x, y in cs]) for fn in transforms)


def infer_T(input_grid):
    """Latent mask: dict {(r, c): new_color} of cells to overwrite."""
    g = input_grid
    band = _legend_band(g)
    T = {}
    if band is None:
        return T
    c0, c1 = band
    shapes = _legend_shapes(g, c0, c1)

    for (r0, cc0) in _find_panels(g, c0, c1):
        border = g[r0][cc0]
        inner = frozenset(
            (rr - (r0 + 1), cc - (cc0 + 1))
            for rr in range(r0 + 1, r0 + 4)
            for cc in range(cc0 + 1, cc0 + 4)
            if g[rr][cc] == 1
        )
        if border == 2 and inner:
            # pattern panel -> solid fill with matching legend color
            sims = _symmetries(inner)
            color = None
            for col, sh in shapes.items():
                if sh in sims:
                    color = col
                    break
            if color is None:
                continue
            for rr in range(r0, r0 + 5):
                for cc in range(cc0, cc0 + 5):
                    T[(rr, cc)] = color
        else:
            # solid panel -> color-2 border + legend glyph of its color in 1s
            color = border
            shape = shapes.get(color)
            if shape is None:
                continue
            for rr in range(r0, r0 + 5):
                for cc in range(cc0, cc0 + 5):
                    T[(rr, cc)] = 2
            for (dr, dc) in shape:
                T[(r0 + 1 + dr, cc0 + 1 + dc)] = 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
