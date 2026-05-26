"""Canonical solver for ARC puzzle 045e512c.

Rule:
  The grid contains one "main" shape (the connected component with the most
  cells) plus several smaller "marker" strokes of distinct colors. Each marker
  encodes a DIRECTION: the sign of its position relative to the main shape's
  bounding box (orthogonal or diagonal). The main shape's footprint is stamped
  repeatedly, recolored to the marker's color, stepping by (shape_size+1) along
  that direction, filling toward the grid edge (a final copy may be clipped).
  The main shape itself is left unchanged.

  infer_T builds the latent mask {(r,c): new_color} of all stamped cells;
  apply_T copies the input and overwrites only those cells.
"""


def _objects(g):
    """8-connected same-color components: list of (color, cells)."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    res = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and not seen[r][c]:
                col = g[r][c]
                st = [(r, c)]
                cells = []
                seen[r][c] = True
                while st:
                    a, b = st.pop()
                    cells.append((a, b))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            na, nb = a + dr, b + dc
                            if 0 <= na < H and 0 <= nb < W and not seen[na][nb] and g[na][nb] == col:
                                seen[na][nb] = True
                                st.append((na, nb))
                res.append((col, cells))
    return res


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    objs = _objects(input_grid)
    T = {}
    if not objs:
        return T

    # Main shape = the largest connected component.
    main = max(objs, key=lambda o: len(o[1]))
    mcells = main[1]
    rs = [p[0] for p in mcells]
    cs = [p[1] for p in mcells]
    mr0, mc0, mr1, mc1 = min(rs), min(cs), max(rs), max(cs)
    h = mr1 - mr0 + 1
    w = mc1 - mc0 + 1
    # Footprint of the shape relative to its top-left corner.
    rel = [(r - mr0, c - mc0) for r, c in mcells]

    for col, cells in objs:
        if cells is mcells:
            continue
        r = [p[0] for p in cells]
        c = [p[1] for p in cells]
        r0, c0, r1, c1 = min(r), min(c), max(r), max(c)

        # Direction = sign of marker position relative to main bbox.
        dr = 1 if r0 > mr1 else (-1 if r1 < mr0 else 0)
        dc = 1 if c0 > mc1 else (-1 if c1 < mc0 else 0)
        if dr == 0 and dc == 0:
            continue

        step_r = (h + 1) * dr
        step_c = (w + 1) * dc

        k = 1
        while k <= max(H, W):
            tr = mr0 + step_r * k
            tc = mc0 + step_c * k
            any_in = False
            for er, ec in rel:
                rr, cc = tr + er, tc + ec
                if 0 <= rr < H and 0 <= cc < W:
                    T[(rr, cc)] = col
                    any_in = True
            if not any_in:
                break
            k += 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
