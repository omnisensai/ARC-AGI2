"""Canonical solver for ARC puzzle 6350f1f4.

Structure: the grid is a regular array of equal-size blocks separated by
0-lines. Color 5 is noise sprinkled over everything (including the separator
lines). Among the blocks there is one recurring two-color tile (the "pattern"),
solid blocks of the pattern's dominant color ("main"), and solid blocks of the
pattern's minority color ("accent").

Rule: every solid-accent block is replaced by the clean pattern tile; every
other block becomes solid main; separator lines are cleaned back to 0. The
pattern is recovered by per-cell majority vote across the (noisy) pattern
blocks, which removes the 5-noise.
"""

NOISE = 5


def _seps(g):
    H, W = len(g), len(g[0])
    seprow = [r for r in range(H) if all(g[r][c] in (0, NOISE) for c in range(W))]
    sepcol = [c for c in range(W) if all(g[r][c] in (0, NOISE) for r in range(H))]
    return seprow, sepcol


def _bounds(seps, sz):
    b, p = [], 0
    for s in seps + [sz]:
        if s > p:
            b.append((p, s))
        p = s + 1
    return b


def infer_T(input_grid):
    """Compute the overwrite mask T as {(r, c): new_color}."""
    g = input_grid
    H, W = len(g), len(g[0])
    seprow, sepcol = _seps(g)
    rb, cb = _bounds(seprow, H), _bounds(sepcol, W)
    bh, bw = rb[0][1] - rb[0][0], cb[0][1] - cb[0][0]

    blocks = {}
    for bi, (r0, r1) in enumerate(rb):
        for bj, (c0, c1) in enumerate(cb):
            blocks[(bi, bj)] = [[g[r][c] for c in range(c0, c1)] for r in range(r0, r1)]

    # all real colors (ignore separator 0 and noise 5)
    colors = set()
    for b in blocks.values():
        for row in b:
            for v in row:
                if v not in (0, NOISE):
                    colors.add(v)

    # pattern blocks contain >=2 distinct real colors; vote each cell to denoise
    pat_blocks = [b for b in blocks.values()
                  if len({v for row in b for v in row if v not in (0, NOISE)}) >= 2]
    pattern = [[None] * bw for _ in range(bh)]
    for r in range(bh):
        for c in range(bw):
            cnt = {}
            for b in pat_blocks:
                v = b[r][c]
                if v != NOISE:
                    cnt[v] = cnt.get(v, 0) + 1
            if cnt:
                pattern[r][c] = max(cnt, key=cnt.get)

    # main = dominant color in pattern, accent = the other
    pc = {}
    for row in pattern:
        for v in row:
            if v is not None:
                pc[v] = pc.get(v, 0) + 1
    main = max(pc, key=pc.get)
    accent_cands = [c for c in colors if c != main]
    accent = accent_cands[0] if accent_cands else main

    solid_main = [[main] * bw for _ in range(bh)]

    T = {}
    for (bi, bj), b in blocks.items():
        r0, c0 = rb[bi][0], cb[bj][0]
        nz = [v for row in b for v in row if v != NOISE]
        is_solid_accent = bool(nz) and all(v == accent for v in nz)
        target = pattern if is_solid_accent else solid_main
        for r in range(bh):
            for c in range(bw):
                T[(r0 + r, c0 + c)] = target[r][c]

    # separator lines always cleaned back to 0 (strip noise that landed on them)
    sr, sc = set(seprow), set(sepcol)
    for r in range(H):
        for c in range(W):
            if r in sr or c in sc:
                T[(r, c)] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
