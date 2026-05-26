def parse_cells(g):
    """Collapse the gridline-separated grid into a coarse cell-grid.

    Separator rows/cols are the fully-uniform lines; the blocks between them
    are uniform color cells (or -1 if mixed, which never happens here)."""
    H, W = len(g), len(g[0])
    rowsep = [r for r in range(H) if len(set(g[r])) == 1]
    colsep = [c for c in range(W) if len(set(g[r][c] for r in range(H))) == 1]

    def runs(n, seps):
        seps = set(seps)
        res = []
        start = 0
        for i in range(n):
            if i in seps:
                if start < i:
                    res.append((start, i))
                start = i + 1
        if start < n:
            res.append((start, n))
        return res

    rr = runs(H, rowsep)
    cc = runs(W, colsep)
    nR, nC = len(rr), len(cc)
    cell = [[0] * nC for _ in range(nR)]
    for ri, (r0, r1) in enumerate(rr):
        for ci, (c0, c1) in enumerate(cc):
            vals = set(g[r][c] for r in range(r0, r1) for c in range(c0, c1))
            cell[ri][ci] = vals.pop() if len(vals) == 1 else -1
    return cell, rr, cc


def infer_T(input_grid):
    """Latent mask: stamp the unique template object (centered on its marker
    color) onto every isolated lone marker cell, clipping at boundaries."""
    g = input_grid
    cell, rr, cc = parse_cells(g)
    nR, nC = len(cell), len(cell[0])

    # 8-connected components of non-zero cells in the coarse grid
    seen = [[False] * nC for _ in range(nR)]
    comps = []
    for r in range(nR):
        for c in range(nC):
            if cell[r][c] != 0 and not seen[r][c]:
                stack = [(r, c)]
                comp = []
                seen[r][c] = True
                while stack:
                    y, x = stack.pop()
                    comp.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            if (0 <= ny < nR and 0 <= nx < nC
                                    and not seen[ny][nx] and cell[ny][nx] != 0):
                                seen[ny][nx] = True
                                stack.append((ny, nx))
                comps.append(comp)

    T = {}
    if not comps:
        return T

    # template = the largest component; its bbox-center color is the marker
    template = max(comps, key=len)
    rs = [y for y, _ in template]
    cs = [x for _, x in template]
    cr = (min(rs) + max(rs)) // 2
    ccn = (min(cs) + max(cs)) // 2
    marker = cell[cr][ccn]
    pat = {(y - cr, x - ccn): cell[y][x] for y, x in template}

    # markers = singleton components whose color equals the marker color
    centers = []
    for comp in comps:
        if comp is template:
            continue
        if len(comp) == 1 and cell[comp[0][0]][comp[0][1]] == marker:
            centers.append(comp[0])

    # stamp the template (clipped) on each marker, in cell coords, then pixels
    cell_changes = {}
    for (mr, mc) in centers:
        for (dy, dx), col in pat.items():
            R, C = mr + dy, mc + dx
            if 0 <= R < nR and 0 <= C < nC:
                cell_changes[(R, C)] = col

    for (R, C), col in cell_changes.items():
        r0, r1 = rr[R]
        c0, c1 = cc[C]
        for r in range(r0, r1):
            for c in range(c0, c1):
                T[(r, c)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
