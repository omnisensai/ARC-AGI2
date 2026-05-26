def _frame_color(g):
    cnt = {}
    for row in g:
        for v in row:
            if v != 0:
                cnt[v] = cnt.get(v, 0) + 1
    return max(cnt, key=lambda c: cnt[c]) if cnt else None


def _boxes(g, frame):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == frame and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if not (0 <= y < H and 0 <= x < W) or seen[y][x] or g[y][x] != frame:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((y + dy, x + dx))
                rs = [a for a, _ in cells]
                cs = [b for _, b in cells]
                comps.append((min(rs), max(rs), min(cs), max(cs)))
    return comps


def _quadrants(g, frame, box):
    """Return {(qi,qj): [(r,c),...]} for the 2x2 interior cells of a box,
    or None if the box is not a 3x3 grid frame."""
    r0, r1, c0, c1 = box
    fr = [r for r in range(r0, r1 + 1)
          if all(g[r][c] == frame for c in range(c0, c1 + 1))]
    fc = [c for c in range(c0, c1 + 1)
          if all(g[r][c] == frame for r in range(r0, r1 + 1))]
    if len(fr) != 3 or len(fc) != 3:
        return None
    quads = {}
    for qi, (ra, rb) in enumerate([(fr[0], fr[1]), (fr[1], fr[2])]):
        for qj, (ca, cb) in enumerate([(fc[0], fc[1]), (fc[1], fc[2])]):
            region = [(r, c) for r in range(ra + 1, rb)
                      for c in range(ca + 1, cb)]
            quads[(qi, qj)] = region
    return quads


def infer_T(input_grid):
    """Latent mask: dict {(r,c): color}.

    The grid holds several rectangular grid-frame boxes (drawn in the most
    common non-zero color). Each box is split by its interior frame lines into
    a 2x2 array of cells. Across all boxes a consistent legend maps each
    quadrant position (TL/TR/BL/BR) to one content color. The transformation
    fills every cell completely with the color for its quadrant position.
    """
    g = input_grid
    H, W = len(g), len(g[0])
    frame = _frame_color(g)
    T = {}
    if frame is None:
        return T

    boxes = _boxes(g, frame)
    box_quads = []
    legend = {}
    for box in boxes:
        q = _quadrants(g, frame, box)
        if q is None:
            continue
        box_quads.append(q)
        for pos, region in q.items():
            for (r, c) in region:
                v = g[r][c]
                if v != 0 and v != frame:
                    legend.setdefault(pos, v)

    for q in box_quads:
        for pos, region in q.items():
            color = legend.get(pos)
            if color is None:
                continue
            for (r, c) in region:
                T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
