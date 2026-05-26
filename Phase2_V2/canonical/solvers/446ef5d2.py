"""Canonical solver for ARC puzzle 446ef5d2.

Rule (derived from ALL train+test pairs):
  The input scatters several connected "jigsaw" pieces over a background.
  One special "marker" color appears exactly 3 times forming an L-tromino that
  touches one corner of the piece it is attached to; that L points at a corner.
  The pieces (with their marker cells removed) tile EXACTLY into a single
  rectangular framed box: the box's whole outer border is the dominant frame
  color, and the marker-bearing piece sits at the box corner the L points to,
  keeping its original grid position. apply_T clears everything and stamps the
  reassembled box back into the grid anchored at the marker piece.

Canonical latent-T form: infer_T computes the latent mask (the reassembled box
and where to stamp it); apply_T copies the input (here a blank background) and
overwrites only the masked cells.
"""
from collections import Counter


def _components(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    res = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if not (0 <= y < H and 0 <= x < W) or seen[y][x] or g[y][x] == bg:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((y + dy, x + dx))
                res.append(cells)
    return res


def infer_T(input_grid):
    """Return (bg, box_grid, box_r0, box_c0): the reassembled box and where it
    is stamped. box_grid is a 2D list (None for unused cells)."""
    g = input_grid
    GH, GW = len(g), len(g[0])
    cnt = Counter(v for row in g for v in row)
    bg = cnt.most_common(1)[0][0]
    nonbg = Counter(v for row in g for v in row if v != bg)
    markers = [k for k, v in nonbg.items() if v == 3]
    marker = markers[0] if markers else None
    frame_cnt = Counter({k: v for k, v in nonbg.items() if k != marker})
    if not frame_cnt:
        return bg, None, 0, 0
    frame = frame_cnt.most_common(1)[0][0]

    pieces = []
    marker_idx = None
    for cells in _components(g, bg):
        non = [(y, x) for y, x in cells if g[y][x] != marker]
        mk = [(y, x) for y, x in cells if g[y][x] == marker]
        if not non:
            continue
        rs = [y for y, x in non]
        cs = [x for y, x in non]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        pdict = {(y - r0, x - c0): g[y][x] for y, x in non}
        corner = None
        if mk:
            mr = sum(y for y, x in mk) / len(mk)
            mc = sum(x for y, x in mk) / len(mk)
            top = mr < (r0 + r1) / 2
            left = mc < (c0 + c1) / 2
            corner = ('T' if top else 'B') + ('L' if left else 'R')
        pieces.append({'d': pdict, 'h': r1 - r0 + 1, 'w': c1 - c0 + 1,
                       'corner': corner, 'tl': (r0, c0)})
        if mk:
            marker_idx = len(pieces) - 1

    if not pieces or marker_idx is None:
        return bg, None, 0, 0

    total = sum(len(p['d']) for p in pieces)
    maxh = max(p['h'] for p in pieces)
    maxw = max(p['w'] for p in pieces)
    factors = [(h, total // h) for h in range(maxh, total + 1)
               if total % h == 0 and total // h >= maxw]

    def try_dims(BH, BW):
        mp = pieces[marker_idx]
        corner = mp['corner']
        if corner == 'TL':
            moff = (0, 0)
        elif corner == 'TR':
            moff = (0, BW - mp['w'])
        elif corner == 'BL':
            moff = (BH - mp['h'], 0)
        else:
            moff = (BH - mp['h'], BW - mp['w'])
        if moff[0] < 0 or moff[1] < 0:
            return None
        filled = [[False] * BW for _ in range(BH)]
        grid = [[None] * BW for _ in range(BH)]
        used = [False] * len(pieces)
        pkeys = [sorted(p['d'].keys()) for p in pieces]

        def is_border(R, C):
            return R == 0 or R == BH - 1 or C == 0 or C == BW - 1

        def place(i, orr, occ):
            added = []
            for (y, x), v in pieces[i]['d'].items():
                R, C = y + orr, x + occ
                if not (0 <= R < BH and 0 <= C < BW) or filled[R][C]:
                    return None
                if is_border(R, C) and v != frame:
                    return None
                added.append((R, C, v))
            return added

        added = place(marker_idx, *moff)
        if added is None:
            return None
        for R, C, v in added:
            filled[R][C] = True
            grid[R][C] = v
        used[marker_idx] = True
        result = [None]

        def first_empty():
            for r in range(BH):
                for c in range(BW):
                    if not filled[r][c]:
                        return (r, c)
            return None

        def rec():
            if result[0] is not None:
                return
            fe = first_empty()
            if fe is None:
                result[0] = [row[:] for row in grid]
                return
            fr, fc = fe
            for i in range(len(pieces)):
                if used[i]:
                    continue
                y0, x0 = pkeys[i][0]
                orr, occ = fr - y0, fc - x0
                ad = place(i, orr, occ)
                if ad is None:
                    continue
                for R, C, v in ad:
                    filled[R][C] = True
                    grid[R][C] = v
                used[i] = True
                rec()
                if result[0] is not None:
                    return
                used[i] = False
                for R, C, v in ad:
                    filled[R][C] = False
                    grid[R][C] = None

        rec()
        if result[0] is None:
            return None
        return result[0], moff

    for BH, BW in factors:
        r = try_dims(BH, BW)
        if r:
            grid, moff = r
            mtl = pieces[marker_idx]['tl']
            return bg, grid, mtl[0] - moff[0], mtl[1] - moff[1]
    return bg, None, 0, 0


def apply_T(input_grid, T):
    bg, box_grid, box_r0, box_c0 = T
    GH, GW = len(input_grid), len(input_grid[0])
    out = [[bg] * GW for _ in range(GH)]
    if box_grid is None:
        return out
    for r in range(len(box_grid)):
        for c in range(len(box_grid[0])):
            v = box_grid[r][c]
            if v is None:
                continue
            R, C = box_r0 + r, box_c0 + c
            if 0 <= R < GH and 0 <= C < GW:
                out[R][C] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
