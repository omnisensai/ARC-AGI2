from collections import Counter


def _base_edge(g):
    """The border holding the most markers anchors all lines."""
    H = len(g)
    W = len(g[0])
    e = {
        'top': sum(1 for c in range(W) if g[0][c]),
        'bot': sum(1 for c in range(W) if g[H - 1][c]),
        'left': sum(1 for r in range(H) if g[r][0]),
        'right': sum(1 for r in range(H) if g[r][W - 1]),
    }
    return max(e, key=e.get)


def infer_T(input_grid):
    """Infer a sparse mask {(r,c): value}.

    Lines run perpendicular to the base edge (the border with the most
    markers) and are anchored on it. In each line the color that appears
    twice (the "pair") defines a period p and the lattice phase. A third
    odd-colored marker (the "single") may also be present:
      - no single        -> stamp the pair color on every lattice point.
      - single on-lattice -> recolor lattice points from the base up to and
                             including the single with the single's color;
                             leave points beyond the single blank.
      - single off-lattice -> stamp the pair color on every lattice point
                              and preserve the single in place.
    """
    g = input_grid
    H = len(g)
    W = len(g[0])
    be = _base_edge(g)
    horizontal = be in ('left', 'right')
    if horizontal:
        nlines, L = H, W
    else:
        nlines, L = W, H

    def rc(line, t):
        if be == 'left':
            return (line, t)
        if be == 'right':
            return (line, W - 1 - t)
        if be == 'top':
            return (t, line)
        return (H - 1 - t, line)  # bot

    Tcells = {}
    for line in range(nlines):
        mk = []
        for t in range(L):
            r, c = rc(line, t)
            v = g[r][c]
            if v:
                mk.append((t, v))
        if not mk:
            continue
        cnt = Counter(v for _, v in mk)
        paircolors = [k for k, v in cnt.items() if v >= 2]
        if not paircolors:
            continue
        pc = paircolors[0]
        pair_t = sorted(t for t, v in mk if v == pc)
        base_t = pair_t[0]
        p = pair_t[1] - pair_t[0]
        if p == 0:
            continue
        lattice = list(range(base_t, L, p))
        single = [(t, v) for t, v in mk if v != pc]
        if not single:
            for t in lattice:
                r, c = rc(line, t)
                Tcells[(r, c)] = pc
        else:
            st, sc = single[0]
            if (st - base_t) % p == 0:
                for t in lattice:
                    if t <= st:
                        r, c = rc(line, t)
                        Tcells[(r, c)] = sc
            else:
                for t in lattice:
                    r, c = rc(line, t)
                    Tcells[(r, c)] = pc
                r, c = rc(line, st)
                Tcells[(r, c)] = sc
    return Tcells


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
