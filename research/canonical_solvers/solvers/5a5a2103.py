def infer_T(input_grid):
    """Infer a latent mask {(r,c): color}.

    The grid is split into 4x4 cells by full separator lines (one color).
    Most non-empty cells hold a solid 2x2 block of a 'label' color sitting in
    their interior; exactly one cell holds a distinctive 'template' shape.
    Each cell-row carries one label color. The transformation stamps the
    template shape into EVERY cell, recolored to that cell-row's label color
    (and clears any other pre-existing content inside those cells).
    """
    g = input_grid
    H, W = len(g), len(g[0])

    # separator color = the color forming a full row (or column) line
    sep = None
    for r in range(H):
        if len(set(g[r])) == 1:
            sep = g[r][0]
            break
    if sep is None:
        for c in range(W):
            col = [g[r][c] for r in range(H)]
            if len(set(col)) == 1:
                sep = col[0]
                break

    seprows = [r for r in range(H) if all(g[r][c] == sep for c in range(W))]
    sepcols = [c for c in range(W) if all(g[r][c] == sep for r in range(H))]

    def ranges(seps, N):
        res = []
        prev = 0
        for s in seps:
            if s > prev:
                res.append((prev, s))
            prev = s + 1
        if prev < N:
            res.append((prev, N))
        return res

    rr = ranges(seprows, H)
    cr = ranges(sepcols, W)

    def cell_content(rrng, crng):
        return [[g[r][c] for c in range(crng[0], crng[1])]
                for r in range(rrng[0], rrng[1])]

    def is_solid_2x2_block(blk):
        ch, cw = len(blk), len(blk[0])
        nz = [(i, j, blk[i][j]) for i in range(ch) for j in range(cw) if blk[i][j] != 0]
        if len(nz) != 4:
            return None
        colors = set(v for _, _, v in nz)
        if len(colors) != 1:
            return None
        rs = sorted(set(i for i, _, _ in nz))
        cs = sorted(set(j for _, j, _ in nz))
        if len(rs) == 2 and len(cs) == 2 and rs[1] - rs[0] == 1 and cs[1] - cs[0] == 1:
            return nz[0][2]
        return None

    template = None      # list of (i,j) cells (relative to a cell) of the shape
    row_color = {}       # cell-row index -> label color
    for ri, rrng in enumerate(rr):
        for crng in cr:
            blk = cell_content(rrng, crng)
            nz = [(i, j) for i in range(len(blk)) for j in range(len(blk[0])) if blk[i][j] != 0]
            if not nz:
                continue
            bc = is_solid_2x2_block(blk)
            if bc is not None:
                row_color[ri] = bc
            else:
                template = nz

    T = {}
    if template is None:
        return T
    tmplset = set(template)
    for ri, rrng in enumerate(rr):
        col = row_color.get(ri)
        if col is None:
            continue
        ch = rrng[1] - rrng[0]
        for crng in cr:
            cw = crng[1] - crng[0]
            for i in range(ch):
                for j in range(cw):
                    pos = (rrng[0] + i, crng[0] + j)
                    if (i, j) in tmplset:
                        T[pos] = col
                    else:
                        T[pos] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
