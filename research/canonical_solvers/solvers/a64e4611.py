"""Canonical solver for ARC puzzle a64e4611.

Rule (same-size grids, background 0, a single noise color):
  The grid is a field of sparse noise tiles separated by blank "corridors".
  There is always a vertical blank corridor (some column is entirely blank) and
  sometimes a horizontal blank corridor (some row entirely blank). These split
  the grid; within the side/top/bottom regions there may be additional blank
  "arms" (a band of rows blank across a side, or a band of cols blank across the
  top/bottom). The transformation paints color 3 over the INTERIOR of every such
  corridor/arm — the blank band eroded by one cell on every side that borders
  noise (grid edges are not eroded). Arms additionally merge across the main
  corridor's interior so the painted shape is a connected plus/cross.

`infer_T` builds the latent fill mask (set of (r,c) to recolor to 3) from the
input structure alone; `apply_T` copies the input and overwrites the masked
cells with 3.
"""

FILL = 3


def _runs(idxs):
    """Maximal contiguous integer runs as (start, end) inclusive pairs."""
    out, cur = [], []
    for x in sorted(idxs):
        if cur and x == cur[-1] + 1:
            cur.append(x)
        else:
            if cur:
                out.append((cur[0], cur[-1]))
            cur = [x]
    if cur:
        out.append((cur[0], cur[-1]))
    return out


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    blank = [[input_grid[r][c] == 0 for c in range(W)] for r in range(H)]
    col_blank = [sum(blank[r][c] for r in range(H)) for c in range(W)]
    row_blank = [sum(blank[r][c] for c in range(W)) for r in range(H)]

    Tv = 0.8 * H  # column "still a corridor" blank-count threshold
    Th = 0.8 * W

    mask = set()

    # ---- main vertical corridor: band around the fully blank column(s) ----
    full_cols = [c for c in range(W) if col_blank[c] == H]
    vc0 = vc1 = None
    if full_cols:
        a, b = max(_runs(full_cols), key=lambda t: t[1] - t[0])
        while a - 1 >= 0 and col_blank[a - 1] >= Tv:
            a -= 1
        while b + 1 < W and col_blank[b + 1] >= Tv:
            b += 1
        vc0, vc1 = a, b

    # ---- main horizontal corridor: band around the fully blank row(s) ----
    full_rows = [r for r in range(H) if row_blank[r] == W]
    hr0 = hr1 = None
    if full_rows:
        a, b = max(_runs(full_rows), key=lambda t: t[1] - t[0])
        while a - 1 >= 0 and row_blank[a - 1] >= Th:
            a -= 1
        while b + 1 < H and row_blank[b + 1] >= Th:
            b += 1
        hr0, hr1 = a, b

    # vertical corridor fill: interior cols, blank-rect row-range eroded vs noise
    if vc0 is not None:
        band_rows = [r for r in range(H)
                     if all(blank[r][c] for c in range(vc0, vc1 + 1))]
        Vr0, Vr1 = max(_runs(band_rows), key=lambda t: t[1] - t[0])
        top = Vr0 + (1 if Vr0 > 0 else 0)
        bot = Vr1 - (1 if Vr1 < H - 1 else 0)
        for r in range(top, bot + 1):
            for c in range(vc0 + 1, vc1):
                mask.add((r, c))

    # horizontal corridor fill: interior rows, blank-rect col-range eroded vs noise
    if hr0 is not None:
        band_cols = [c for c in range(W)
                     if all(blank[r][c] for r in range(hr0, hr1 + 1))]
        Hc0, Hc1 = max(_runs(band_cols), key=lambda t: t[1] - t[0])
        left = Hc0 + (1 if Hc0 > 0 else 0)
        right = Hc1 - (1 if Hc1 < W - 1 else 0)
        for c in range(left, right + 1):
            for r in range(hr0 + 1, hr1):
                mask.add((r, c))

    # ---- horizontal arms: blank-row gaps within the left / right regions ----
    if vc0 is not None:
        ci0, ci1 = vc0 + 1, vc1 - 1  # vertical-corridor interior columns
        regions = [((0, vc0 - 1), (0, ci1)),          # left arm
                   ((vc1 + 1, W - 1), (ci0, W - 1))]   # right arm
        for (rc0, rc1), (ac0, ac1) in regions:
            if rc0 > rc1:
                continue
            br = [r for r in range(H)
                  if all(blank[r][c] for c in range(rc0, rc1 + 1))]
            for a, b in _runs(br):
                if b - a < 2:
                    continue  # too thin to have an interior
                for r in range(a + 1, b):
                    for c in range(ac0, ac1 + 1):
                        mask.add((r, c))

    # ---- vertical arms: blank-col gaps within the top / bottom regions ----
    if hr0 is not None:
        ri0, ri1 = hr0 + 1, hr1 - 1  # horizontal-corridor interior rows
        regions = [((0, hr0 - 1), (0, ri1)),          # top arm
                   ((hr1 + 1, H - 1), (ri0, H - 1))]   # bottom arm
        for (rr0, rr1), (ar0, ar1) in regions:
            if rr0 > rr1:
                continue
            bc = [c for c in range(W)
                  if all(blank[r][c] for r in range(rr0, rr1 + 1))]
            for a, b in _runs(bc):
                if b - a < 2:
                    continue
                for c in range(a + 1, b):
                    for r in range(ar0, ar1 + 1):
                        mask.add((r, c))

    return mask


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c) in T:
        out[r][c] = FILL
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
