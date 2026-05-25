def infer_T(input_grid):
    """Latent mask: a rotated-diamond ("X / nested wedge") field radiating from one
    end of a color sequence, with the three back wedges capped by wall markers.

    Input structure (read from the grid alone):
      * One straight line of DISTINCT colors -- the "sequence".
      * Up to two MARKER pairs (two adjacent equal-colored cells) sitting on grid
        walls.  Each marker pair contributes a fill color for one direction.

    Construction (in 45-degree rotated coordinates a = (c-CC)-(r-CR),
    b = (c-CC)+(r-CR) measured from the sequence's interior end CENTER):
      * ring = min(|a|, |b|); diamond value = seq[ring] (seq read from the center
        outward, color 0 when ring exceeds the sequence length).
      * The two diagonal ARMS (a==0 or b==0) and the FILL wedge (the wedge the
        sequence points into) show the full diamond.
      * The OPPOSITE wedge is entirely the marker on that wall (else background 0).
      * The two SIDE wedges show the diamond only on the single "bleed" line
        (ring 1, on the axis whose sign matches the fill wedge) that continues a
        fill-wedge arm; beyond it they take their wall marker (else 0).

    The latent mask T overwrites every cell with this reconstructed value.
    """
    H, W = len(input_grid), len(input_grid[0])
    nz = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != 0]

    # --- marker pairs: two adjacent equal-colored cells (they live on walls) ---
    markers = []
    used = set()
    for (r, c) in nz:
        for dr, dc in ((0, 1), (1, 0)):
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < H and 0 <= c2 < W and input_grid[r2][c2] == input_grid[r][c]:
                markers.append(((r, c), (r2, c2), input_grid[r][c]))
                used.add((r, c))
                used.add((r2, c2))

    # --- the sequence: the remaining non-zero cells lie in one row or one column ---
    seqcells = [(r, c) for (r, c) in nz if (r, c) not in used]
    rows = set(r for r, c in seqcells)
    if len(rows) == 1:
        seqcells.sort(key=lambda x: x[1])      # horizontal
    else:
        seqcells.sort(key=lambda x: x[0])      # vertical

    e1, e2 = seqcells[0], seqcells[-1]

    def on_edge(p):
        r, c = p
        return r in (0, H - 1) or c in (0, W - 1)

    # center = the sequence end NOT on a grid edge (the colors radiate from it)
    if on_edge(e2) and not on_edge(e1):
        center, far = e1, e2
        order = seqcells
    elif on_edge(e1) and not on_edge(e2):
        center, far = e2, e1
        order = seqcells[::-1]
    else:
        center, far = e1, e2
        order = seqcells

    seq = [input_grid[r][c] for r, c in order]
    CR, CC = center

    def wedge(r, c):
        a = (c - CC) - (r - CR)
        b = (c - CC) + (r - CR)
        if a == 0 or b == 0:
            return 'arm', a, b
        if a > 0 and b > 0:
            return 'R', a, b
        if a < 0 and b < 0:
            return 'L', a, b
        if a > 0 and b < 0:
            return 'T', a, b
        return 'B', a, b

    # fill direction = the wedge the sequence points into (center -> far)
    fr, fc = far
    da, db = (fc - CC) - (fr - CR), (fc - CC) + (fr - CR)
    if da > 0 and db > 0:
        fill = 'R'
    elif da < 0 and db < 0:
        fill = 'L'
    elif da > 0 and db < 0:
        fill = 'T'
    elif da < 0 and db > 0:
        fill = 'B'
    else:
        if abs(fr - CR) >= abs(fc - CC):
            fill = 'B' if fr > CR else 'T'
        else:
            fill = 'R' if fc > CC else 'L'

    # marker color for each wall/wedge
    wallcolor = {}
    for (m1, m2, col) in markers:
        mr = (m1[0] + m2[0]) / 2.0
        mc = (m1[1] + m2[1]) / 2.0
        a = (mc - CC) - (mr - CR)
        b = (mc - CC) + (mr - CR)
        if a > 0 and b > 0:
            w = 'R'
        elif a < 0 and b < 0:
            w = 'L'
        elif a > 0 and b < 0:
            w = 'T'
        elif a < 0 and b > 0:
            w = 'B'
        else:
            if abs(mr - CR) >= abs(mc - CC):
                w = 'B' if mr > CR else 'T'
            else:
                w = 'R' if mc > CC else 'L'
        wallcolor[w] = col

    opp = {'R': 'L', 'L': 'R', 'T': 'B', 'B': 'T'}[fill]
    fa = {'R': 1, 'T': 1, 'L': -1, 'B': -1}      # sign of a inside fill wedge
    fb = {'R': 1, 'T': -1, 'L': -1, 'B': 1}      # sign of b inside fill wedge
    L = len(seq)

    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            w, a, b = wedge(r, c)
            m = min(abs(a), abs(b))
            dd = seq[m] if m < L else None
            keep = (w == 'arm' or w == fill)
            if (not keep) and w != opp and m == 1:
                if abs(a) == 1 and (1 if a > 0 else -1) == fa[fill]:
                    keep = True
                if abs(b) == 1 and (1 if b > 0 else -1) == fb[fill]:
                    keep = True
            if keep:
                T[r][c] = dd if dd is not None else 0
            else:
                T[r][c] = wallcolor.get(w, 0)
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
