"""Canonical latent-T solver for ARC puzzle f9a67cb5.

Structure: the grid contains straight walls made of 8s (either full rows or
full columns) that each have one or more gaps (background cells). A single
marker cell of color 2 sits on a grid edge and a "stream" of color 2 flows
inward, perpendicular to the walls. The stream travels straight until it
reaches the line adjacent to the next wall, where it spreads (parallel to the
wall) until it reaches a gap on each side -- the nearest gap, or the grid edge
if there is no gap on that side. It then passes through every gap it covers and
continues; each gap becomes a new independent stream. After the last wall the
stream runs straight to the far edge.

infer_T traces this flow from the input alone and returns a latent mask
(dict of {(r,c): 2}); apply_T copies the input and paints only the masked
cells.
"""


def _stream_span(s, gaps, maxidx):
    """Span [L,R] a single stream at coordinate `s` spreads to before a wall.

    If the stream aligns with a gap it passes straight through (span = {s}).
    Otherwise it reaches the nearest gap on each side, or the grid edge if no
    gap exists on that side.
    """
    gs = set(gaps)
    if s in gs:
        return s, s
    left = [x for x in gaps if x < s]
    L = max(left) if left else 0
    right = [x for x in gaps if x > s]
    R = min(right) if right else maxidx
    return L, R


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Locate the single marker of color 2 (the stream source on an edge).
    start = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 2:
                start = (r, c)
                break
        if start is not None:
            break
    if start is None:
        return {}
    sr, sc = start

    # Detect walls: a full row or full column made mostly of 8s.
    row_walls = [r for r in range(H)
                 if sum(1 for v in input_grid[r] if v == 8) > W // 2]
    col_walls = [c for c in range(W)
                 if sum(1 for r in range(H) if input_grid[r][c] == 8) > H // 2]

    if row_walls and not col_walls:
        vertical = True            # walls are rows -> flow vertical
    elif col_walls and not row_walls:
        vertical = False           # walls are columns -> flow horizontal
    else:
        vertical = (sr == 0 or sr == H - 1)

    cells = {(sr, sc)}

    if vertical:
        down = (sr == 0)
        walls = [w for w in sorted(row_walls) if (w > sr if down else w < sr)]
        if not down:
            walls = walls[::-1]
        streams = [sc]
        cur = sr
        for w in walls:
            adj = w - 1 if down else w + 1
            # straight travel of each stream up to the row adjacent to the wall
            for s in streams:
                lo, hi = sorted((cur, adj))
                for rr in range(lo, hi + 1):
                    cells.add((rr, s))
            gaps = [c for c in range(W) if input_grid[w][c] == 0]
            covered = set()
            for s in streams:
                L, R = _stream_span(s, gaps, W - 1)
                for cc in range(L, R + 1):
                    cells.add((adj, cc))
                    covered.add(cc)
            used = sorted(x for x in gaps if x in covered)
            for x in used:
                cells.add((w, x))
            streams = used
            cur = w
        edge = H - 1 if down else 0
        for s in streams:
            lo, hi = sorted((cur, edge))
            for rr in range(lo, hi + 1):
                cells.add((rr, s))
    else:
        right = (sc == 0)
        walls = [w for w in sorted(col_walls) if (w > sc if right else w < sc)]
        if not right:
            walls = walls[::-1]
        streams = [sr]
        cur = sc
        for w in walls:
            adj = w - 1 if right else w + 1
            for s in streams:
                lo, hi = sorted((cur, adj))
                for cc in range(lo, hi + 1):
                    cells.add((s, cc))
            gaps = [r for r in range(H) if input_grid[r][w] == 0]
            covered = set()
            for s in streams:
                L, R = _stream_span(s, gaps, H - 1)
                for rr in range(L, R + 1):
                    cells.add((rr, adj))
                    covered.add(rr)
            used = sorted(x for x in gaps if x in covered)
            for x in used:
                cells.add((x, w))
            streams = used
            cur = w
        edge = W - 1 if right else 0
        for s in streams:
            lo, hi = sorted((cur, edge))
            for cc in range(lo, hi + 1):
                cells.add((s, cc))

    return {(r, c): 2 for (r, c) in cells}


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
