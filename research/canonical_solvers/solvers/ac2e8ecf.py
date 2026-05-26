"""Canonical latent-T solver for ARC puzzle ac2e8ecf.

Rule (derived from ALL pairs):
  The grid contains scattered single-color objects of two kinds:
    - BOXES: hollow rectangles (filled perimeter, empty interior).
    - PLUS shapes: anything else (plus / arrow-like glyphs).
  Each object keeps its columns but moves vertically:
    - BOXES gravitate UP, stacking against the top edge / other boxes.
    - PLUS shapes gravitate DOWN, stacking against the bottom edge / other pluses.
  Boxes fall first (topmost box settles highest); pluses fall next
  (bottom-most plus settles lowest). Collision is resolved per-column so
  objects sharing columns stack rather than overlap.

The latent transformation T is the mask {(r,c): new_color} of every cell that
must change: the original object cells are cleared (set to background 0) and the
destination cells are painted. apply_T copies the input and overwrites T's cells.
"""


def _components(g):
    """8-connected same-color components (objects)."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and not seen[r][c]:
                col = g[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W:
                        continue
                    if seen[y][x] or g[y][x] != col:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy or dx:
                                stack.append((y + dy, x + dx))
                rs = [a for a, _ in cells]
                cs = [b for _, b in cells]
                objs.append({
                    'col': col,
                    'r0': min(rs), 'c0': min(cs),
                    'r1': max(rs), 'c1': max(cs),
                    'cells': cells,
                })
    return objs


def _is_box(o):
    """A box = hollow rectangle: cells exactly equal the bbox perimeter."""
    perim = set()
    for c in range(o['c0'], o['c1'] + 1):
        perim.add((o['r0'], c))
        perim.add((o['r1'], c))
    for r in range(o['r0'], o['r1'] + 1):
        perim.add((r, o['c0']))
        perim.add((r, o['c1']))
    return set(o['cells']) == perim and (o['r1'] - o['r0']) >= 1 and (o['c1'] - o['c0']) >= 1


def infer_T(input_grid):
    """Compute the latent transformation mask from input structure alone."""
    H, W = len(input_grid), len(input_grid[0])
    objs = _components(input_grid)
    boxes = [o for o in objs if _is_box(o)]
    pluses = [o for o in objs if not _is_box(o)]

    occ = [[False] * W for _ in range(H)]   # cells claimed by settled objects
    dest = {}                               # (r,c) -> color of object destinations

    # Boxes gravitate up; topmost first so it settles at the very top.
    boxes.sort(key=lambda o: o['r0'])
    for o in boxes:
        shift = 0
        for newtop in range(0, o['r0'] + 1):
            s = o['r0'] - newtop
            if all((y - s) >= 0 and not occ[y - s][x] for (y, x) in o['cells']):
                shift = s
                break
        for (y, x) in o['cells']:
            ny = y - shift
            occ[ny][x] = True
            dest[(ny, x)] = o['col']

    # Plus shapes gravitate down; bottom-most first so it settles at the bottom.
    pluses.sort(key=lambda o: -o['r1'])
    for o in pluses:
        shift = 0
        for newbot in range(H - 1, o['r1'] - 1, -1):
            s = newbot - o['r1']
            if all((y + s) < H and not occ[y + s][x] for (y, x) in o['cells']):
                shift = s
                break
        for (y, x) in o['cells']:
            ny = y + shift
            occ[ny][x] = True
            dest[(ny, x)] = o['col']

    # Latent mask T: clear every original object cell, then paint destinations.
    T = {}
    for o in objs:
        for (y, x) in o['cells']:
            T[(y, x)] = 0
    for (rc, col) in dest.items():
        T[rc] = col
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
