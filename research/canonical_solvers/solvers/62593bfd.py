"""Canonical latent-T solver for ARC puzzle 62593bfd.

Rule (same-size grid):
  The grid contains several monochrome objects on a uniform background.  Every
  object keeps its exact shape and its column span, but slides vertically until
  it is flush against one of the horizontal edges.  Which edge it sticks to is
  an intrinsic property of the object's SHAPE (orientation-independent):

    * If the object is a single orthogonally-connected piece whose cell count is
      NOT a small 4/5/6-cell "bend", it rises and sits flush against the TOP
      edge (row 0).
    * Otherwise -- small 4/5/6-cell bends, and shapes whose cells are only
      diagonally linked (rings / diamonds / octagons, i.e. >1 orthogonal
      component) -- it sinks and sits flush against the BOTTOM edge (row H-1).

The latent transformation T is the dict {(r, c): new_color}: it clears every
vacated object cell (back to the background colour) and paints every
destination cell.  apply_T copies the input and overwrites only those masked
cells.
"""

from collections import Counter, deque


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
    """8-connected monochrome-aware components of non-background cells."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if not (0 <= rr < H and 0 <= cc < W) or seen[rr][cc] or g[rr][cc] == bg:
                        continue
                    seen[rr][cc] = True
                    cells.append((rr, cc, g[rr][cc]))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((rr + dr, cc + dc))
                objs.append(cells)
    return objs


def _ortho_components(cellset):
    """Number of 4-connected (orthogonal) components within a set of cells."""
    seen = set()
    n = 0
    for s in cellset:
        if s in seen:
            continue
        n += 1
        dq = deque([s])
        while dq:
            r, c = dq.popleft()
            if (r, c) in seen or (r, c) not in cellset:
                continue
            seen.add((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                dq.append((r + dr, c + dc))
    return n


def _goes_top(cells):
    """Decide the destination edge from the object's shape alone."""
    pts = set((r, c) for r, c, _ in cells)
    n = len(pts)
    ortho_connected = _ortho_components(pts) == 1
    return ortho_connected and n not in (4, 5, 6)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg(input_grid)
    T = {}
    for cells in _objects(input_grid, bg):
        rs = [r for r, c, v in cells]
        r0, r1 = min(rs), max(rs)
        shift = -r0 if _goes_top(cells) else (H - 1) - r1
        for r, c, v in cells:          # clear vacated cells
            T[(r, c)] = bg
        for r, c, v in cells:          # paint moved cells (override clears)
            T[(r + shift, c)] = v
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out
