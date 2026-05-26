"""Canonical latent-T solver for ARC puzzle 90f3ed37.

Rule
----
The grid contains several connected "stamp" objects drawn in a single
foreground color on a background. Exactly one of them is the *complete*
template: it extends all the way to the right edge of the grid. Every other
object is the same motif but with its right-reaching arms truncated.

The template, read column by column, is a horizontally periodic motif: each
column holds a set of row offsets, and the motif repeats with some period as
it marches toward the right edge. To complete a partial object we continue it
rightward from its own rightmost column to the right edge, placing cells at the
row offsets dictated by the template's pattern for that (phase-aligned) column,
measured relative to the partial object's own top-left anchor. The newly added
cells are painted with the fill color (1).

infer_T computes the set of cells to paint (the latent mask); apply_T copies
the input and overwrites only those cells.
"""

from collections import defaultdict

FILL = 1  # color used to draw the completed (extended) portion


def _components(grid, color):
    """8-connected components of cells equal to `color`."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] != color:
                        continue
                    seen.add((a, b))
                    comp.append((a, b))
                    for da in (-1, 0, 1):
                        for db in (-1, 0, 1):
                            if da or db:
                                stack.append((a + da, b + db))
                comps.append(comp)
    return comps


def infer_T(input_grid):
    """Return a dict {(r, c): FILL} of cells to add (the latent mask)."""
    H, W = len(input_grid), len(input_grid[0])

    # background = most common color; object color = the salient non-bg color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    fg_candidates = [v for v in counts if v != bg]
    if not fg_candidates:
        return {}
    obj_color = max(fg_candidates, key=lambda v: counts[v])

    objs = _components(input_grid, obj_color)
    if not objs:
        return {}

    # Template = the object that already reaches the rightmost column.
    templates = [o for o in objs if max(c for _, c in o) == W - 1]
    if not templates:
        return {}
    tmpl = max(templates, key=len)

    tr0 = min(r for r, _ in tmpl)
    tc0 = min(c for _, c in tmpl)
    # Per-(relative-)column set of row offsets for the template motif.
    tcol = defaultdict(set)
    for r, c in tmpl:
        tcol[c - tc0].add(r - tr0)

    T = {}
    for o in objs:
        if o is tmpl:
            continue
        or0 = min(r for r, _ in o)
        oc0 = min(c for _, c in o)
        omaxc = max(c for _, c in o)
        # Continue rightward to the edge using the template's column pattern,
        # phase-aligned by relative column, anchored at this object's top row.
        for c in range(omaxc + 1, W):
            relc = c - oc0
            if relc in tcol:
                for off in tcol[relc]:
                    rr = or0 + off
                    if 0 <= rr < H and input_grid[rr][c] == bg:
                        T[(rr, c)] = FILL
    return T


def apply_T(input_grid, T):
    """Copy input, overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
