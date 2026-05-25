"""Canonical latent-T solver for ARC puzzle 4ff4c9da.

Rule
----
The grid is a doubly-periodic "outer-product" pattern: every background cell value
equals f(rowtype[r], coltype[c]), where a row's type is its full content and a
column's type is its full content. A few cells are overwritten with the marker
colour 8, forming one or more small connected shapes (markers).

Each marker is replicated across the symmetries of the underlying clean pattern:

  * Translations: a marker may be shifted by (dr, dc) when the clean background,
    over the marker's footprint padded by one cell, is preserved by that shift.
    The two axes are checked independently (a row-shift must preserve the
    background over the marker's column strip; a col-shift over its row strip),
    so a marker can translate independently along each axis.
  * Reflections: a marker may also be mirrored across an axis, but ONLY when its
    own shape is symmetric under that mirror (so the placed copy keeps the same
    orientation). Asymmetric markers are translated only.

The latent transformation mask T is the dict of cells that must become 8 (the
source markers together with all their valid images). apply_T copies the input
and paints exactly those cells with 8.
"""


def _row_types(grid):
    """Group identical rows (treating 8 as a wildcard); return per-row class id."""
    H, W = len(grid), len(grid[0])

    def eq(i, j):
        for c in range(W):
            a, b = grid[i][c], grid[j][c]
            if a == 8 or b == 8:
                continue
            if a != b:
                return False
        return True

    grp = [-1] * H
    gid = 0
    for i in range(H):
        if grp[i] == -1:
            grp[i] = gid
            for j in range(i + 1, H):
                if grp[j] == -1 and eq(i, j):
                    grp[j] = gid
            gid += 1
    return grp


def _types(grid, axis):
    if axis == 'col':
        grid = [list(col) for col in zip(*grid)]
    return _row_types(grid)


def _restore_bg(grid):
    """Reconstruct the clean background (each marker cell replaced by the most
    common value seen at its (rowtype, coltype) class)."""
    H, W = len(grid), len(grid[0])
    rt = _types(grid, 'row')
    ct = _types(grid, 'col')
    counts = {}
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v == 8:
                continue
            key = (rt[r], ct[c])
            d = counts.setdefault(key, {})
            d[v] = d.get(v, 0) + 1
    bg = [[0] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v != 8:
                bg[r][c] = v
            else:
                d = counts.get((rt[r], ct[c]))
                bg[r][c] = max(d, key=d.get) if d else v
    return bg


def _clusters8(cells):
    """8-connected connected components of the given cell set."""
    cells = set(cells)
    seen = set()
    out = []
    for start in cells:
        if start in seen:
            continue
        stack = [start]
        comp = []
        while stack:
            x = stack.pop()
            if x in seen or x not in cells:
                continue
            seen.add(x)
            comp.append(x)
            r, c = x
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr or dc:
                        stack.append((r + dr, c + dc))
        out.append(comp)
    return out


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _restore_bg(input_grid)
    markers = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]

    T = {}
    R = 1  # one-cell pad around each marker for the local background-match check
    for cl in _clusters8(markers):
        for (r, c) in cl:
            T[(r, c)] = 8  # keep every source marker cell
        rows = sorted({r for r, c in cl})
        cols = sorted({c for r, c in cl})
        minr, maxr = min(rows), max(rows)
        minc, maxc = min(cols), max(cols)
        cellset = set(cl)

        # A reflection along an axis is allowed only if the marker's own shape is
        # symmetric under that reflection (so orientation is preserved).
        row_sym = all((minr + maxr - r, c) in cellset for (r, c) in cl)
        col_sym = all((r, minc + maxc - c) in cellset for (r, c) in cl)

        frows = [r for r in range(minr - R, maxr + R + 1) if 0 <= r < H]
        fcols = [c for c in range(minc - R, maxc + R + 1) if 0 <= c < W]

        # candidate 1D affine maps  i -> s*i + o   (s=1 translation, s=-1 reflection)
        rmaps = [(1, sh) for sh in range(-H, H + 1)]
        if row_sym:
            rmaps += [(-1, a) for a in range(0, 2 * H - 1)]
        cmaps = [(1, sh) for sh in range(-W, W + 1)]
        if col_sym:
            cmaps += [(-1, a) for a in range(0, 2 * W - 1)]

        # valid row maps: preserve clean background over the column strip + pad
        row_ok = []
        for m in rmaps:
            if not all(0 <= m[0] * r + m[1] < H for r in rows):
                continue
            good = True
            for r in frows:
                rr = m[0] * r + m[1]
                if not (0 <= rr < H):
                    good = False
                    break
                for c in fcols:
                    if bg[r][c] != bg[rr][c]:
                        good = False
                        break
                if not good:
                    break
            if good:
                row_ok.append(m)

        # valid col maps: preserve clean background over the row strip + pad
        col_ok = []
        for m in cmaps:
            if not all(0 <= m[0] * c + m[1] < W for c in cols):
                continue
            good = True
            for c in fcols:
                cc = m[0] * c + m[1]
                if not (0 <= cc < W):
                    good = False
                    break
                for r in frows:
                    if bg[r][c] != bg[r][cc]:
                        good = False
                        break
                if not good:
                    break
            if good:
                col_ok.append(m)

        for rm in row_ok:
            for cm in col_ok:
                for (r, c) in cl:
                    T[(rm[0] * r + rm[1], cm[0] * c + cm[1])] = 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
