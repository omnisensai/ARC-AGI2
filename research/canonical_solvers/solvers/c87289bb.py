"""Canonical latent-T solver for ARC puzzle c87289bb.

Structure of the input:
  * Several vertical "bars" of color 8 occupy the top rows in fixed columns.
  * A single horizontal row contains one or more contiguous runs ("segments")
    of color 2.

Transformation:
  * Every bar is extended downward to the bottom of the grid, EXCEPT bars whose
    column lies within a 2-segment: those are "capped" at the row just above the
    2-row (they only extend one cell past the top block).
  * For each 2-segment a vertical wall of 8 is grown from the row above the
    segment down to the bottom:
      - a LEFT wall at (start-1) when the segment's left end sits on a bar;
      - a RIGHT wall at (end+1) when the segment's right end sits on a bar OR a
        bar lies strictly inside the segment.
  * Each wall is connected to the structure by a short horizontal top edge along
    the row above the 2-row, running inward from the wall until the first bar
    column it meets (inclusive).

infer_T returns the latent mask (dict of cell -> 8); apply_T overwrites only the
masked cells.
"""


def infer_T(input_grid):
    g = input_grid
    H = len(g)
    W = len(g[0]) if H else 0
    T = {}
    if H == 0 or W == 0:
        return T

    # Columns that hold a bar (color 8 present in the top row).
    barcols = sorted(c for c in range(W) if g[0][c] == 8)
    if not barcols:
        return T
    barset = set(barcols)

    # Height of the bars: consecutive top rows fully filled across all bar cols.
    barheight = 0
    for r in range(H):
        if all(g[r][c] == 8 for c in barcols):
            barheight = r + 1
        else:
            break

    # Row that carries the color-2 segments.
    r2 = None
    for r in range(H):
        if any(g[r][c] == 2 for c in range(W)):
            r2 = r
            break
    if r2 is None:
        return T

    # Contiguous runs of 2 on that row.
    segs = []
    c = 0
    while c < W:
        if g[r2][c] == 2:
            s = c
            while c < W and g[r2][c] == 2:
                c += 1
            segs.append((s, c - 1))
        else:
            c += 1

    in_seg = set()
    for s, e in segs:
        for cc in range(s, e + 1):
            in_seg.add(cc)

    def mark(r, cc):
        if 0 <= r < H and 0 <= cc < W and g[r][cc] == 0:
            T[(r, cc)] = 8

    top = r2 - 1  # row just above the 2-row (top edge of the boxes)

    # Extend bars downward (capped if the bar sits inside a 2-segment).
    for col in barcols:
        bottom = top if col in in_seg else (H - 1)
        for r in range(barheight, bottom + 1):
            mark(r, col)

    # Grow walls + top edges for each segment.
    for s, e in segs:
        # Left wall when the segment starts on a bar.
        if s in barset:
            wc = s - 1
            if 0 <= wc < W:
                for r in range(top, H):
                    mark(r, wc)
                cc = wc
                while cc <= e:
                    mark(top, cc)
                    if cc != wc and cc in barset:
                        break
                    cc += 1
        # Right wall when the segment ends on a bar or contains an interior bar.
        if (e in barset) or any(bc in barset for bc in range(s + 1, e)):
            wc = e + 1
            if 0 <= wc < W:
                for r in range(top, H):
                    mark(r, wc)
                cc = wc
                while cc >= s:
                    mark(top, cc)
                    if cc != wc and cc in barset:
                        break
                    cc -= 1

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
