"""Canonical solver for ARC puzzle a096bf4d.

Structure: the grid is a 2D array of framed blocks separated by all-zero
border rows/columns. Every block has the same small interior pattern (a
global "base" template). A few blocks carry a marker: a single interior cell
whose color differs from the base. Markers of the same color sit at the same
interior position, so they form a logical (block-row x block-col) layer.

Rule: within each interior-position layer, markers of the same color that
share a block-row are connected by filling every block between them along that
row; markers that share a block-column are connected by filling every block
between them along that column. (Drawing the segment between collinear marker
pairs.) Isolated markers stay as-is. Everything else is copied unchanged.
"""

from collections import Counter


def _grid_ranges(g):
    H, W = len(g), len(g[0])
    zr = [r for r in range(H) if all(v == 0 for v in g[r])]
    zc = [c for c in range(W) if all(g[r][c] == 0 for r in range(H))]

    def ranges(zeros, n):
        res, seg = [], []
        for i in range(n):
            if i in zeros:
                if seg:
                    res.append((seg[0], seg[-1]))
                    seg = []
            else:
                seg.append(i)
        if seg:
            res.append((seg[0], seg[-1]))
        return res

    return ranges(zr, H), ranges(zc, W)


def _interior_cell(g, rseg, cseg, a, b):
    return g[rseg[0] + 1 + a][cseg[0] + 1 + b]


def infer_T(input_grid):
    """Return a latent mask {(r,c): new_color} of cells to overwrite."""
    g = input_grid
    rr, cc = _grid_ranges(g)
    if not rr or not cc:
        return {}
    ih = rr[0][1] - rr[0][0] - 1
    iw = cc[0][1] - cc[0][0] - 1
    nR, nC = len(rr), len(cc)

    T = {}
    for a in range(ih):
        for b in range(iw):
            # global base color at this interior position (majority over blocks)
            cnt = Counter(
                _interior_cell(g, rr[R], cc[C], a, b)
                for R in range(nR) for C in range(nC)
            )
            base = cnt.most_common(1)[0][0]

            # collect markers at this position, grouped by color
            bycolor = {}
            for R in range(nR):
                for C in range(nC):
                    v = _interior_cell(g, rr[R], cc[C], a, b)
                    if v != base:
                        bycolor.setdefault(v, []).append((R, C))

            # value grid for this layer (start from input, fill segments)
            layer = [
                [_interior_cell(g, rr[R], cc[C], a, b) for C in range(nC)]
                for R in range(nR)
            ]
            for color, pts in bycolor.items():
                rows, cols = {}, {}
                for R, C in pts:
                    rows.setdefault(R, []).append(C)
                    cols.setdefault(C, []).append(R)
                for R, Cs in rows.items():
                    if len(Cs) >= 2:
                        for c in range(min(Cs), max(Cs) + 1):
                            layer[R][c] = color
                for C, Rs in cols.items():
                    if len(Rs) >= 2:
                        for r in range(min(Rs), max(Rs) + 1):
                            layer[r][C] = color

            # record changed cells into the mask
            for R in range(nR):
                for C in range(nC):
                    orig = _interior_cell(g, rr[R], cc[C], a, b)
                    if layer[R][C] != orig:
                        gr = rr[R][0] + 1 + a
                        gc = cc[C][0] + 1 + b
                        T[(gr, gc)] = layer[R][C]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
