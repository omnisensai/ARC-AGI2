"""Canonical solver for ARC puzzle 9f669b64.

Rule (same-size grid):
  The grid contains three colored objects lying along a single axis (vertical or
  horizontal). The MIDDLE object is the "mover" (a solid rectangle). One end is the
  "anchor" (the irregular shape, or — when both ends are rectangles — the end whose
  cross-width equals the mover's), the other end is the "target" (a solid rectangle).
  The mover slides away from the anchor, passing THROUGH the target until it reaches
  the grid boundary. The target splits into two halves perpendicular to the motion,
  each half shifting outward by (mover_cross_width // 2) to open a gap the width of
  the mover; the gap becomes background.

infer_T computes a latent mask T: a dict {(r,c): new_color} of cells to overwrite.
apply_T copies the input and overwrites only the masked cells.
"""


def find_objects(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                col = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if not (0 <= a < H and 0 <= b < W) or seen[a][b] or grid[a][b] != col:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                rs = [x for x, _ in cells]
                cs = [y for _, y in cells]
                objs.append({
                    'color': col, 'cells': set(cells),
                    'r0': min(rs), 'r1': max(rs), 'c0': min(cs), 'c1': max(cs),
                    'n': len(cells),
                })
    return objs


def is_rect(o):
    return o['n'] == (o['r1'] - o['r0'] + 1) * (o['c1'] - o['c0'] + 1)


def infer_T(grid):
    H, W = len(grid), len(grid[0])
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    objs = find_objects(grid, bg)
    T = {}
    if len(objs) != 3:
        return T

    cr = [(o['r0'] + o['r1']) / 2 for o in objs]
    cc = [(o['c0'] + o['c1']) / 2 for o in objs]
    vertical = (max(cr) - min(cr)) >= (max(cc) - min(cc))
    key = (lambda o: (o['r0'] + o['r1']) / 2) if vertical \
        else (lambda o: (o['c0'] + o['c1']) / 2)

    order = sorted(objs, key=key)
    mover = order[1]
    ends = [order[0], order[2]]

    if vertical:
        mw = mover['c1'] - mover['c0'] + 1          # perpendicular extent (columns)
    else:
        mw = mover['r1'] - mover['r0'] + 1          # perpendicular extent (rows)

    def perpw(o):
        return (o['c1'] - o['c0'] + 1) if vertical else (o['r1'] - o['r0'] + 1)

    rect0, rect1 = is_rect(ends[0]), is_rect(ends[1])
    if rect0 and not rect1:
        anchor, target = ends[1], ends[0]
    elif rect1 and not rect0:
        anchor, target = ends[0], ends[1]
    else:
        # Both rectangles: anchor is the end whose cross-width equals the mover's.
        if perpw(ends[0]) == mw and perpw(ends[1]) != mw:
            anchor, target = ends[0], ends[1]
        elif perpw(ends[1]) == mw and perpw(ends[0]) != mw:
            anchor, target = ends[1], ends[0]
        elif perpw(ends[0]) >= perpw(ends[1]):
            target, anchor = ends[0], ends[1]
        else:
            target, anchor = ends[1], ends[0]

    half = mw // 2

    # Clear original mover and target cells (gap / vacated regions become bg).
    for (r, c) in mover['cells']:
        T[(r, c)] = bg
    for (r, c) in target['cells']:
        T[(r, c)] = bg

    if vertical:
        moving_toward_top = key(target) < key(mover)
        mc = (mover['c0'] + mover['c1']) / 2
        # Split target into two halves about the mover's center, shift outward.
        for (r, c) in target['cells']:
            nc = c - half if c <= mc - 0.5 else c + half
            if 0 <= nc < W:
                T[(r, nc)] = target['color']
        # Slide mover along the axis to the grid edge in its travel direction.
        mh = mover['r1'] - mover['r0'] + 1
        nr0 = 0 if moving_toward_top else H - mh
        for (r, c) in mover['cells']:
            T[(nr0 + (r - mover['r0']), c)] = mover['color']
    else:
        moving_toward_left = key(target) < key(mover)
        mr = (mover['r0'] + mover['r1']) / 2
        for (r, c) in target['cells']:
            nr = r - half if r <= mr - 0.5 else r + half
            if 0 <= nr < H:
                T[(nr, c)] = target['color']
        mwid = mover['c1'] - mover['c0'] + 1
        nc0 = 0 if moving_toward_left else W - mwid
        for (r, c) in mover['cells']:
            T[(r, nc0 + (c - mover['c0']))] = mover['color']

    return T


def apply_T(grid, T):
    out = [row[:] for row in grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
