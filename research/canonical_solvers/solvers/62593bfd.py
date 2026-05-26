"""Canonical latent-T solver for ARC puzzle 62593bfd.

Rule (same-size grid):
  The grid holds several monochrome shapes on a uniform background, each in its
  own column band.  Every shape keeps its exact form and its columns but slides
  vertically until it is flush against a horizontal edge.  Which edge it sticks
  to is decided by whether the shape has a CONGRUENT TWIN among the other shapes
  (a second shape with the same form, up to rotation/reflection):

    * shapes that DO have a congruent twin rise and sit flush against the TOP
      edge (top of bounding box -> row 0);
    * shapes that are UNIQUE (no congruent twin) sink and sit flush against the
      BOTTOM edge (bottom of bounding box -> row H-1).

The latent transformation T is a dict {(r, c): new_color} giving every
destination cell with its colour; apply_T starts from a cleared (background)
grid and paints those cells.
"""

from collections import Counter


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def _bg(g):
    cnt = Counter()
    for row in g:
        for v in row:
            cnt[v] += 1
    return cnt.most_common(1)[0][0]


def _objects(g, bg):
    """8-connected monochrome components of non-background cells."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                color = g[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if seen[rr][cc] or g[rr][cc] != color:
                        continue
                    seen[rr][cc] = True
                    cells.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((rr + dr, cc + dc))
                objs.append((color, cells))
    return objs


def _norm(cells):
    r0 = min(r for r, c in cells)
    c0 = min(c for r, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _transforms(s):
    """All 8 dihedral orientations of a normalized cell set."""
    res = set()
    cur = s
    for _ in range(4):
        cur = _norm(frozenset((c, -r) for r, c in cur))      # rotate 90
        res.add(cur)
        res.add(_norm(frozenset((r, -c) for r, c in cur)))   # plus mirror
    return res


def _has_twin(i, objs, norms, forms):
    cells_i = objs[i][1]
    for j in range(len(objs)):
        if j == i:
            continue
        if len(objs[j][1]) != len(cells_i):
            continue
        if norms[j] in forms[i]:
            return True
    return False


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg(input_grid)
    objs = _objects(input_grid, bg)
    norms = [_norm(cells) for _, cells in objs]
    forms = [_transforms(n) for n in norms]

    T = {}
    for i, (color, cells) in enumerate(objs):
        rs = [r for r, c in cells]
        r0, r1 = min(rs), max(rs)
        if _has_twin(i, objs, norms, forms):
            shift = -r0             # top edge to row 0
        else:
            shift = (H - 1) - r1    # bottom edge to last row
        for r, c in cells:
            T[(r + shift, c)] = color
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg(input_grid)
    out = [[bg] * W for _ in range(H)]
    for (r, c), color in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = color
    return out
