"""Canonical solver for ARC puzzle 5b692c0f.

Rule: every connected object contains a straight line of color 4 that acts as a
mirror axis (vertical or horizontal). The object is meant to be symmetric across
that axis, but one half is corrupted (cells missing / extra). The clean half is
the one with more foreground cells; it is reflected across the axis onto the
corrupt half, repairing the object into a perfectly symmetric figure.

Canonical latent-T form: infer_T builds a {(r,c): color} overwrite mask from the
input structure (objects -> 4-axis -> reflect clean half); apply_T copies the
input and writes only the masked cells.
"""

from collections import Counter


def _find_objects(g):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and not seen[r][c]:
                comp = []
                st = [(r, c)]
                seen[r][c] = True
                while st:
                    cr, cc = st.pop()
                    comp.append((cr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < H and 0 <= nc < W and g[nr][nc] != 0 and not seen[nr][nc]:
                                seen[nr][nc] = True
                                st.append((nr, nc))
                objs.append(comp)
    return objs


def _find_axis(g, comp):
    """Return ('V', col) or ('H', row): the line carrying the most color-4 cells."""
    c4 = [(r, c) for r, c in comp if g[r][c] == 4]
    if not c4:
        return None
    colc = Counter(c for r, c in c4)
    rowc = Counter(r for r, c in c4)
    best_col, best_col_n = colc.most_common(1)[0]
    best_row, best_row_n = rowc.most_common(1)[0]
    return ('V', best_col) if best_col_n >= best_row_n else ('H', best_row)


def infer_T(input_grid):
    """Build the latent overwrite mask {(r,c): color}."""
    g = input_grid
    H, W = len(g), len(g[0])
    T = {}
    for comp in _find_objects(g):
        ax = _find_axis(g, comp)
        if ax is None:
            continue
        kind, a = ax
        rows = [r for r, c in comp]
        cols = [c for r, c in comp]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        if kind == 'V':
            left = sum(1 for r, c in comp if c < a)
            right = sum(1 for r, c in comp if c > a)
            src_left = left >= right
            for r in range(r0, r1 + 1):
                for k in range(W):
                    lc, rc = a - k, a + k
                    if 0 <= lc < W and 0 <= rc < W:
                        if src_left:
                            T[(r, rc)] = g[r][lc]
                        else:
                            T[(r, lc)] = g[r][rc]
        else:
            top = sum(1 for r, c in comp if r < a)
            bot = sum(1 for r, c in comp if r > a)
            src_top = top >= bot
            for c in range(c0, c1 + 1):
                for k in range(H):
                    ur, dr = a - k, a + k
                    if 0 <= ur < H and 0 <= dr < H:
                        if src_top:
                            T[(dr, c)] = g[ur][c]
                        else:
                            T[(ur, c)] = g[dr][c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
