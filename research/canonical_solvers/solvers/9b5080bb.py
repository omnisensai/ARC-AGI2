"""Canonical latent-T solver for ARC puzzle 9b5080bb.

Rule
----
The grid contains a frame color and two rectangular panels, each with its own
background color, that host filled "blob" shapes drawn in a single shared blob
color. Every blob is an almost-perfect filled rectangle marred by 1-cell
defects on its boundary:

  * NOTCH  - a panel-background cell intruding one step into the blob (a cell
             of the host bg color, inside the blob's bounding box, that has
             exactly one neighbor of the bg color and three blob neighbors).
  * SPIKE  - a blob cell protruding one step out of the rectangle (the lone
             blob cell occupying an extreme row/column of the bounding box).

For each defect the transformation paints a 2-cell mark, crossing the blob's
edge: the defect cell itself plus its unique same-type neighbor (for a notch,
the outward bg neighbor; for a spike, the inward blob neighbor). The paint
color is the background color of the OTHER host panel.

The latent mask T maps {(r, c): new_color}; apply_T overwrites only those cells.
"""

from collections import Counter, deque


def _components(g, col):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == col and not seen[r][c]:
                q = deque([(r, c)])
                seen[r][c] = True
                cells = []
                while q:
                    y, x = q.popleft()
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and g[ny][nx] == col and not seen[ny][nx]:
                            seen[ny][nx] = True
                            q.append((ny, nx))
                comps.append(cells)
    return comps


def _find_blob_color(g):
    """Blob color = the color forming several small, dense, fully-enclosed rectangles."""
    H, W = len(g), len(g[0])
    cnt = Counter(v for row in g for v in row)
    best = None
    for col in cnt:
        comps = _components(g, col)
        if len(comps) < 2:
            continue
        good = 0
        for cells in comps:
            rs = [y for y, x in cells]
            cs = [x for y, x in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            area = (r1 - r0 + 1) * (c1 - c0 + 1)
            dens = len(cells) / area
            if 0.7 < dens <= 1.05 and len(cells) >= 4 and r0 > 0 and c0 > 0 and r1 < H - 1 and c1 < W - 1:
                good += 1
        if good >= 2:
            tot = sum(len(c) for c in comps)
            if best is None or tot < best[1]:
                best = (col, tot)
    return best[0] if best else None


def _host_bg(g, cells, blob):
    """Background color of the panel containing this blob (commonest non-blob neighbor)."""
    H, W = len(g), len(g[0])
    cset = set(cells)
    nb = Counter()
    for (y, x) in cells:
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and (ny, nx) not in cset and g[ny][nx] != blob:
                nb[g[ny][nx]] += 1
    return nb.most_common(1)[0][0] if nb else None


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    blob = _find_blob_color(g)
    T = {}
    if blob is None:
        return T

    blobs = []
    for cells in _components(g, blob):
        rs = [y for y, x in cells]
        cs = [x for y, x in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        area = (r1 - r0 + 1) * (c1 - c0 + 1)
        if len(cells) / area > 0.4 and len(cells) >= 4:
            blobs.append((cells, (r0, r1, c0, c1)))

    hosts = [_host_bg(g, cells, blob) for cells, _ in blobs]
    distinct = list(dict.fromkeys(hosts))

    def mark_color(h):
        other = [x for x in distinct if x != h]
        return other[0] if other else h

    for cells, (r0, r1, c0, c1) in blobs:
        hb = _host_bg(g, cells, blob)
        mk = mark_color(hb)

        # NOTCH: a host-bg cell inside the bbox with exactly one bg neighbor (3 blob).
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if g[r][c] != hb:
                    continue
                same = []
                bl = 0
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = r + dy, c + dx
                    v = g[ny][nx] if 0 <= ny < H and 0 <= nx < W else None
                    if v == hb:
                        same.append((ny, nx))
                    elif v == blob:
                        bl += 1
                if len(same) == 1 and bl == 3:
                    T[(r, c)] = mk
                    T[same[0]] = mk

        # SPIKE: an extreme bbox edge (top/bottom row, left/right col) holding a
        # single blob cell; paint it plus its unique blob neighbor.
        rows, cols = {}, {}
        for (r, c) in cells:
            rows.setdefault(r, []).append((r, c))
            cols.setdefault(c, []).append((r, c))
        cand = set()
        for edge in (rows.get(r0, []), rows.get(r1, []), cols.get(c0, []), cols.get(c1, [])):
            if len(edge) == 1:
                cand.add(edge[0])
        for (r, c) in cand:
            nb = [(r + dy, c + dx) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= r + dy < H and 0 <= c + dx < W and g[r + dy][c + dx] == blob]
            if len(nb) == 1:
                T[(r, c)] = mk
                T[nb[0]] = mk

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
