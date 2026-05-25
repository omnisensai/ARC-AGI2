from collections import Counter, defaultdict

# Puzzle 4ff4c9da.
#
# The grid is a self-similar pattern carved into rectangular content "blocks"
# by full-length separator lines (rows/cols of a single repeated color).  A
# few cells have been overwritten with the colour 8, forming one or more small
# marker objects.  Each marker covers cells of one underlying ("object") colour
# inside its block.  The transformation copies the marker onto every block where
# that same object colour forms the same local shape (block-bounded window),
# leaving everything else untouched.
#
# infer_T reconstructs the clean background, locates the markers, and builds the
# latent mask of every cell that must become 8.  apply_T overwrites only those.

_NB8 = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)]


def _reconstruct_background(inp):
    """Recover the clean (8-free) background grid."""
    H, W = len(inp), len(inp[0])
    g = [row[:] for row in inp]

    def overlap_eq(a, b):
        for x, y in zip(a, b):
            if x == 8 or y == 8:
                continue
            if x != y:
                return False
        return True

    def consensus_fill(g):
        # cluster identical rows, vote per column, fill remaining 8s
        rlab = [-1] * H
        reps = []
        for r in range(H):
            for i, rep in enumerate(reps):
                if overlap_eq(g[r], g[rep]):
                    rlab[r] = i
                    break
            if rlab[r] < 0:
                rlab[r] = len(reps)
                reps.append(r)
        for lab in set(rlab):
            rows = [r for r in range(H) if rlab[r] == lab]
            for c in range(W):
                cnt = Counter(g[r][c] for r in rows if g[r][c] != 8)
                if cnt:
                    v = cnt.most_common(1)[0][0]
                    for r in rows:
                        if g[r][c] == 8:
                            g[r][c] = v
        # same for columns
        clab = [-1] * W
        creps = []
        for c in range(W):
            colc = [g[r][c] for r in range(H)]
            for i, cr in enumerate(creps):
                if overlap_eq(colc, [g[r][cr] for r in range(H)]):
                    clab[c] = i
                    break
            if clab[c] < 0:
                clab[c] = len(creps)
                creps.append(c)
        for lab in set(clab):
            cols = [c for c in range(W) if clab[c] == lab]
            for r in range(H):
                cnt = Counter(g[r][c] for c in cols if g[r][c] != 8)
                if cnt:
                    v = cnt.most_common(1)[0][0]
                    for c in cols:
                        if g[r][c] == 8:
                            g[r][c] = v
        return g

    for _ in range(3):
        # the background is transpose-symmetric: copy from the mirror cell
        changed = True
        while changed:
            changed = False
            for r in range(H):
                for c in range(W):
                    if g[r][c] == 8 and r < W and c < H and g[c][r] != 8:
                        g[r][c] = g[c][r]
                        changed = True
        g = consensus_fill(g)

    return g


def _partition(n, seps):
    """Maximal runs of non-separator indices -> content blocks."""
    res, cur = [], []
    for i in range(n):
        if i in seps:
            if cur:
                res.append(cur)
                cur = []
        else:
            cur.append(i)
    if cur:
        res.append(cur)
    return res


def _fill_marked_blocks(g, RB, CB, sr, sc):
    """Fill any background cells still hidden by markers using the fact that
    blocks of the same (meta-row, meta-col) class are identical."""
    H, W = len(g), len(g[0])

    def block(rb, cb):
        return [[g[r][c] for c in cb] for r in rb]

    def bmatch(A, B):
        for ra, rb in zip(A, B):
            for a, b in zip(ra, rb):
                if a == 8 or b == 8:
                    continue
                if a != b:
                    return False
        return True

    for _ in range(3):
        blocks = {(I, J): block(rb, cb)
                  for I, rb in enumerate(RB) for J, cb in enumerate(CB)}
        # meta-row classes
        ml = [-1] * len(RB)
        mr = []
        for I in range(len(RB)):
            for k, rep in enumerate(mr):
                if all(bmatch(blocks[(I, J)], blocks[(rep, J)])
                       for J in range(len(CB))):
                    ml[I] = k
                    break
            if ml[I] < 0:
                ml[I] = len(mr)
                mr.append(I)
        # meta-col classes
        nc = [-1] * len(CB)
        mc = []
        for J in range(len(CB)):
            for k, rep in enumerate(mc):
                if all(bmatch(blocks[(I, J)], blocks[(I, rep)])
                       for I in range(len(RB))):
                    nc[J] = k
                    break
            if nc[J] < 0:
                nc[J] = len(mc)
                mc.append(J)
        # vote per (class, in-block position)
        votes = defaultdict(lambda: defaultdict(Counter))
        for I, rb in enumerate(RB):
            for J, cb in enumerate(CB):
                for i, r in enumerate(rb):
                    for j, c in enumerate(cb):
                        if g[r][c] != 8:
                            votes[(ml[I], nc[J])][(i, j)][g[r][c]] += 1
        for I, rb in enumerate(RB):
            for J, cb in enumerate(CB):
                for i, r in enumerate(rb):
                    for j, c in enumerate(cb):
                        if g[r][c] == 8:
                            cnt = votes[(ml[I], nc[J])][(i, j)]
                            if cnt:
                                g[r][c] = cnt.most_common(1)[0][0]
    return g


def _components(inp):
    """8-connected components of the colour-8 marker cells."""
    H, W = len(inp), len(inp[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if inp[r][c] == 8 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if not (0 <= y < H and 0 <= x < W) or seen[y][x] \
                            or inp[y][x] != 8:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in _NB8:
                        stack.append((y + dy, x + dx))
                comps.append(cells)
    return comps


def _bounds(lo, hi, seps, n):
    """Grow [lo,hi] to the enclosing block, including its bounding separators."""
    a = lo
    while a - 1 >= 0 and (a - 1) not in seps:
        a -= 1
    b = hi
    while b + 1 < n and (b + 1) not in seps:
        b += 1
    return (a - 1 if a - 1 >= 0 else a), (b + 1 if b + 1 < n else b)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    g = _reconstruct_background(input_grid)

    sr = set(r for r in range(H) if len(set(g[r])) == 1)
    sc = set(c for c in range(W) if len(set(g[r][c] for r in range(H))) == 1)
    RB = _partition(H, sr)
    CB = _partition(W, sc)
    g = _fill_marked_blocks(g, RB, CB, sr, sc)

    T = {}
    for cells in _components(input_grid):
        rs = [y for y, x in cells]
        cs = [x for y, x in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        # the underlying object colour(s) the marker covered
        vs = set(g[y][x] for y, x in cells if g[y][x] != 8)
        if not vs:
            continue
        R0, R1 = _bounds(r0, r1, sr, H)
        C0, C1 = _bounds(c0, c1, sc, W)
        bh, bw = R1 - R0 + 1, C1 - C0 + 1
        rel = [(y - R0, x - C0) for y, x in cells]
        # reference mask: which cells of the block carry the object colour
        ref = [[(g[R0 + i][C0 + j] in vs) for j in range(bw)]
               for i in range(bh)]
        for tr in range(H - bh + 1):
            for tc in range(W - bw + 1):
                ok = True
                for i in range(bh):
                    for j in range(bw):
                        cv = g[tr + i][tc + j]
                        if cv == 8:
                            continue
                        if (cv in vs) != ref[i][j]:
                            ok = False
                            break
                    if not ok:
                        break
                if ok:
                    for dy, dx in rel:
                        T[(tr + dy, tc + dx)] = 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
