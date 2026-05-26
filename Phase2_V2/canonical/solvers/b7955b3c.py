"""Canonical solver for ARC puzzle b7955b3c.

Rule
----
The grid is a stack of solid-colour rectangular bars over a single background
colour.  Where bars overlap, the top-most bar's colour is visible.  Colour 8
forms small plus-shaped markers that locally dent / bulge the visible edges of
these bars (the marker straddles a bar boundary).

The transformation erases every 8 and straightens all edges back to clean
rectangles: reconstruct each colour's true rectangle as the bounding box of its
(non-8) cells, recover the stacking order from which colour wins in pairwise
overlaps, then repaint every rectangle bottom-to-top.  The result is identical
to the input except on the cells the markers touched, so we express it as a
latent mask of changed cells.
"""

import itertools
from collections import Counter, deque

MARKER = 8


def _rects_and_bg(input_grid):
    """Background colour and each non-bg colour's true rectangle (bbox of its
    non-marker cells)."""
    H, W = len(input_grid), len(input_grid[0])
    counts = Counter(v for row in input_grid for v in row if v != MARKER)
    bg = counts.most_common(1)[0][0]
    rects = {}
    for col in set(counts) - {bg}:
        cells = [(r, c) for r in range(H) for c in range(W)
                 if input_grid[r][c] == col]
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        rects[col] = (min(rs), max(rs), min(cs), max(cs))
    return bg, rects


def _stacking_edges(input_grid, rects):
    """Pairwise 'on top of' relations inferred from the input overlaps."""
    edges = set()
    for a, b in itertools.permutations(rects, 2):
        ra, rb = rects[a], rects[b]
        r0, r1 = max(ra[0], rb[0]), min(ra[1], rb[1])
        c0, c1 = max(ra[2], rb[2]), min(ra[3], rb[3])
        if r0 > r1 or c0 > c1:
            continue
        cnt = Counter()
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                v = input_grid[r][c]
                if v != MARKER:
                    cnt[v] += 1
        if cnt.get(a, 0) > cnt.get(b, 0):
            edges.add((a, b))  # a sits on top of b
    return edges


def _paint_order(cols, edges):
    """Topological order bottom-to-top (a-on-top-of-b => b painted first)."""
    succ = {c: set() for c in cols}
    indeg = {c: 0 for c in cols}
    for top, bottom in edges:
        if top not in succ[bottom]:
            succ[bottom].add(top)
            indeg[top] += 1
    q = deque(sorted(c for c in cols if indeg[c] == 0))
    order = []
    while q:
        x = q.popleft()
        order.append(x)
        for y in sorted(succ[x]):
            indeg[y] -= 1
            if indeg[y] == 0:
                q.append(y)
    # any leftover (cyclic, shouldn't happen) appended deterministically
    for c in cols:
        if c not in order:
            order.append(c)
    return order


def infer_T(input_grid):
    """Latent mask: {(r,c): new_color} for every cell whose colour changes."""
    H, W = len(input_grid), len(input_grid[0])
    bg, rects = _rects_and_bg(input_grid)
    edges = _stacking_edges(input_grid, rects)
    order = _paint_order(list(rects), edges)

    # Render the clean stack of rectangles.
    rendered = [[bg] * W for _ in range(H)]
    for col in order:
        r0, r1, c0, c1 = rects[col]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                rendered[r][c] = col

    T = {}
    for r in range(H):
        for c in range(W):
            if rendered[r][c] != input_grid[r][c]:
                T[(r, c)] = rendered[r][c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
