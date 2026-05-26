import math


def find_boxes(g):
    """Detect rectangular boxes bordered by color 2; return the colored shape
    (non-0/1/2 cells) inside each box."""
    H = len(g)
    W = len(g[0])
    boxes = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 2:
                continue
            # only start at a top-left corner of a 2-border
            if c > 0 and g[r][c - 1] == 2:
                continue
            if r > 0 and g[r - 1][c] == 2:
                continue
            c2 = c
            while c2 + 1 < W and g[r][c2 + 1] == 2:
                c2 += 1
            r2 = r
            while r2 + 1 < H and g[r2 + 1][c] == 2:
                r2 += 1
            if c2 - c < 2 or r2 - r < 2:
                continue
            # verify the full rectangular border is color 2
            if not (all(g[r][cc] == 2 and g[r2][cc] == 2 for cc in range(c, c2 + 1)) and
                    all(g[rr][c] == 2 and g[rr][c2] == 2 for rr in range(r, r2 + 1))):
                continue
            cells = []
            for rr in range(r + 1, r2):
                for cc in range(c + 1, c2):
                    if g[rr][cc] not in (0, 1, 2):
                        cells.append((rr, cc, g[rr][cc]))
            if cells:
                boxes.append({'rect': (r, c, r2, c2), 'cells': cells, 'col': cells[0][2]})
    return boxes


def infer_T(input_grid):
    """Each box keeps its shape in place but is recolored. Ordering the boxes by
    angle around the global centroid, the colors are cyclically shifted by one:
    box at angular position p receives the color of the box at position p+1."""
    boxes = find_boxes(input_grid)
    T = {}
    if len(boxes) < 2:
        return T
    cents = [((b['rect'][0] + b['rect'][2]) / 2.0,
              (b['rect'][1] + b['rect'][3]) / 2.0) for b in boxes]
    cy = sum(p[0] for p in cents) / len(cents)
    cx = sum(p[1] for p in cents) / len(cents)
    ang = [math.atan2(cents[k][0] - cy, cents[k][1] - cx) for k in range(len(boxes))]
    order = sorted(range(len(boxes)), key=lambda k: ang[k])
    n = len(order)
    for pos in range(n):
        cur = order[pos]
        nxt = order[(pos + 1) % n]
        new_col = boxes[nxt]['col']
        for (rr, cc, _v) in boxes[cur]['cells']:
            T[(rr, cc)] = new_col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
