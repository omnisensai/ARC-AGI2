"""Canonical solver for ARC puzzle 4e45f183.

Rule
----
The 19x19 grid is divided by single 0-separator rows/cols into a 3x3 arrangement
of 5x5 blocks (origins rows/cols {1,7,13}). Each block holds a small motif drawn
in a foreground color on the common background color. Across the 9 blocks there
are exactly 3 distinct motif *shapes* (up to D4 rotation/reflection):

  * CENTER motif  - appears once; fully symmetric (has both an axis-aligned and a
                    diagonal mirror).
  * EDGE motif    - appears 4 times; has an axis-aligned mirror (h or v) but no
                    diagonal mirror.
  * CORNER motif  - appears 4 times; has a diagonal mirror but no axis-aligned
                    mirror.

The output reassembles these motifs into a single 4-fold-symmetric "mandala":

      C E C
      E Z E      Z = center motif (canonical/symmetric form)
      C E C      E = edge motif oriented with its mirror axis along the edge,
                     mass pushed outward; C = corner motif oriented with its
                     diagonal mirror, mass pushed into the outer corner.

infer_T computes, from the input alone, the target color for every cell of all
9 blocks (a {(r,c): color} mask); apply_T overwrites those cells on a copy.
"""

N = 5
RS = [1, 7, 13]
CS = [1, 7, 13]


def _rot(b):
    return [[b[N - 1 - c][r] for c in range(N)] for r in range(N)]


def _hflip(b):
    return [row[::-1] for row in b]


def _vflip(b):
    return b[::-1]


def _transp(b):
    return [[b[c][r] for c in range(N)] for r in range(N)]


def _d4(b):
    cur = [list(r) for r in b]
    uniq = []
    seen = set()
    for _ in range(4):
        for f in (cur, _hflip(cur)):
            t = tuple(map(tuple, f))
            if t not in seen:
                seen.add(t)
                uniq.append([list(r) for r in f])
        cur = _rot(cur)
    return uniq


def _canon(b):
    return min(tuple(map(tuple, f)) for f in _d4(b))


def _has_axis_mirror(b):
    return any(_hflip(f) == f or _vflip(f) == f for f in _d4(b))


def _has_diag_mirror(b):
    return any(_transp(f) == f for f in _d4(b))


def infer_T(input_grid):
    g = input_grid

    def getblock(bi, bj):
        r0, c0 = RS[bi], CS[bj]
        return [[g[r0 + i][c0 + j] for j in range(N)] for i in range(N)]

    # background = most common non-separator color
    cnt = {}
    for row in g:
        for v in row:
            cnt[v] = cnt.get(v, 0) + 1
    cnt_nz = {k: v for k, v in cnt.items() if k != 0}
    bg = max(cnt_nz, key=cnt_nz.get)

    blocks = {(bi, bj): getblock(bi, bj) for bi in range(3) for bj in range(3)}

    # group blocks by canonical motif shape
    classes = {}
    for k, b in blocks.items():
        classes.setdefault(_canon(b), []).append(k)

    center_c = edge_c = corner_c = None
    for c, ks in classes.items():
        rep = [list(r) for r in c]
        ax = _has_axis_mirror(rep)
        di = _has_diag_mirror(rep)
        if len(ks) == 1 and ax and di:
            center_c = c
        elif ax and not di:
            edge_c = c
        elif di and not ax:
            corner_c = c

    rep_center = [list(r) for r in center_c]
    rep_edge = [list(r) for r in edge_c]
    rep_corner = [list(r) for r in corner_c]

    def fg(b):
        return [(r, c) for r in range(N) for c in range(N) if b[r][c] != bg]

    # corner: diagonal-symmetric orientation with mass in top-left corner
    def orient_corner():
        best, bk = None, None
        for f in _d4(rep_corner):
            if _transp(f) != f:
                continue
            cells = fg(f)
            key = (sum(r + c for r, c in cells),
                   sum(r for r, c in cells),
                   tuple(map(tuple, f)))
            if bk is None or key < bk:
                bk, best = key, f
        return best

    # top edge: h-symmetric orientation with mass on top rows
    def orient_edge_top():
        best, bk = None, None
        for f in _d4(rep_edge):
            if _hflip(f) != f:
                continue
            cells = fg(f)
            key = (sum(r for r, c in cells), tuple(map(tuple, f)))
            if bk is None or key < bk:
                bk, best = key, f
        return best

    # left edge: v-symmetric orientation with mass on left columns
    def orient_edge_left():
        best, bk = None, None
        for f in _d4(rep_edge):
            if _vflip(f) != f:
                continue
            cells = fg(f)
            key = (sum(c for r, c in cells), tuple(map(tuple, f)))
            if bk is None or key < bk:
                bk, best = key, f
        return best

    tl = orient_corner()
    top = orient_edge_top()
    left = orient_edge_left()

    ob = {
        (0, 0): tl,
        (0, 2): _hflip(tl),
        (2, 0): _vflip(tl),
        (2, 2): _vflip(_hflip(tl)),
        (0, 1): top,
        (2, 1): _vflip(top),
        (1, 0): left,
        (1, 2): _hflip(left),
        (1, 1): rep_center,
    }

    T = {}
    for bi in range(3):
        for bj in range(3):
            r0, c0 = RS[bi], CS[bj]
            blk = ob[(bi, bj)]
            for i in range(N):
                for j in range(N):
                    T[(r0 + i, c0 + j)] = blk[i][j]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
