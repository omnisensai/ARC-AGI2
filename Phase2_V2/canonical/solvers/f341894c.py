"""Canonical latent-T solver for ARC puzzle f341894c.

Structure: background is 8. Marker cells of color 7 sit around the grid.
Object cells are 1/6 forming dominoes (a 6 paired with an adjacent 1).
Each domino is aligned (in its row, or in its column) with a 7 marker.
The rule: the 6 end of each domino must point toward the aligned 7 marker;
if it points the wrong way, swap the 1 and 6.

infer_T finds the 1/6 connected objects (4-connectivity), determines whether
each object is oriented horizontally or vertically (by which axis's lines all
contain a 7 marker), splits the object into adjacent 1-6 dominoes along that
axis, and records the corrected color for any cell that must change.
apply_T copies the input and overwrites only the recorded cells.
"""


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    OBJ = (1, 6)
    SEVEN = 7

    sevens = [(r, c) for r in range(H) for c in range(W) if g[r][c] == SEVEN]
    sevens_by_row = {}
    sevens_by_col = {}
    for r, c in sevens:
        sevens_by_row.setdefault(r, []).append(c)
        sevens_by_col.setdefault(c, []).append(r)

    # connected objects of 1/6 cells (4-connectivity)
    seen = set()
    objs = []
    for r in range(H):
        for c in range(W):
            if g[r][c] in OBJ and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W) or g[rr][cc] not in OBJ:
                        continue
                    seen.add((rr, cc))
                    comp.append((rr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        stack.append((rr + dr, cc + dc))
                objs.append(comp)

    T = {}  # latent mask: {(r, c): new_color}
    for comp in objs:
        rows = sorted(set(r for r, c in comp))
        cols = sorted(set(c for r, c in comp))
        rows_have = all(r in sevens_by_row for r in rows)
        cols_have = all(c in sevens_by_col for c in cols)

        if rows_have and not cols_have:
            axis = 'H'
        elif cols_have and not rows_have:
            axis = 'V'
        elif rows_have and cols_have:
            # ambiguous: prefer the axis along which dominoes span 2 cells
            axis = 'V' if len(cols) <= len(rows) else 'H'
        else:
            continue

        if axis == 'H':
            lines = {}
            for (r, c) in comp:
                lines.setdefault(r, []).append(c)
            for r, cs in lines.items():
                cs = sorted(cs)
                i = 0
                while i + 1 < len(cs):
                    c1, c2 = cs[i], cs[i + 1]
                    if c2 == c1 + 1 and {g[r][c1], g[r][c2]} == set(OBJ):
                        sevenc = min(sevens_by_row[r],
                                     key=lambda x: min(abs(x - c1), abs(x - c2)))
                        if abs(sevenc - c1) < abs(sevenc - c2):
                            near, far = c1, c2
                        else:
                            near, far = c2, c1
                        T[(r, near)] = 6  # 6 toward the 7 marker
                        T[(r, far)] = 1
                        i += 2
                    else:
                        i += 1
        else:  # axis == 'V'
            lines = {}
            for (r, c) in comp:
                lines.setdefault(c, []).append(r)
            for c, rs in lines.items():
                rs = sorted(rs)
                i = 0
                while i + 1 < len(rs):
                    r1, r2 = rs[i], rs[i + 1]
                    if r2 == r1 + 1 and {g[r1][c], g[r2][c]} == set(OBJ):
                        sevenr = min(sevens_by_col[c],
                                     key=lambda x: min(abs(x - r1), abs(x - r2)))
                        if abs(sevenr - r1) < abs(sevenr - r2):
                            near, far = r1, r2
                        else:
                            near, far = r2, r1
                        T[(near, c)] = 6  # 6 toward the 7 marker
                        T[(far, c)] = 1
                        i += 2
                    else:
                        i += 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
