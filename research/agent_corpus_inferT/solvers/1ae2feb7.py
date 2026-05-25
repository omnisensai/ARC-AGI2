def find_sep(g):
    """Find the separator line: a near-full row or column of one nonzero color."""
    H, W = len(g), len(g[0])
    for c in range(W):
        col = [g[r][c] for r in range(H)]
        nz = [v for v in col if v != 0]
        if nz and len(set(nz)) == 1 and len(nz) >= H - 2:
            return ('col', c)
    for r in range(H):
        row = g[r]
        nz = [v for v in row if v != 0]
        if nz and len(set(nz)) == 1 and len(nz) >= W - 2:
            return ('row', r)
    return None


def _pattern(rev, length):
    """Given the bar cells (rev[0] adjacent to separator, increasing distance),
    return a list of length `length` of the extrapolated colors on the target side.
    Each color c with count k repeats with period k (color at offsets 0,k,2k,...);
    where multiple colors collide, the one nearest the separator wins."""
    counts, nearest = {}, {}
    for i, v in enumerate(rev):
        if v != 0:
            counts[v] = counts.get(v, 0) + 1
            if v not in nearest:
                nearest[v] = i
    out = []
    for off in range(length):
        val, best = 0, None
        for v in counts:
            if off % counts[v] == 0:
                if best is None or nearest[v] < best:
                    best, val = nearest[v], v
        out.append(val)
    return out


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    T = {}
    sep = find_sep(g)
    if sep is None:
        return T
    kind, idx = sep
    if kind == 'col':
        c = idx
        left = sum(1 for r in range(H) for cc in range(c) if g[r][cc] != 0)
        right = sum(1 for r in range(H) for cc in range(c + 1, W) if g[r][cc] != 0)
        if left >= right:
            length = W - 1 - c
            for r in range(H):
                bar = g[r][:c][::-1]          # bar[0] adjacent to separator
                if not any(v != 0 for v in bar):
                    continue
                pat = _pattern(bar, length)
                for off, v in enumerate(pat):
                    T[(r, c + 1 + off)] = v
        else:
            length = c
            for r in range(H):
                bar = g[r][c + 1:]            # bar[0] adjacent to separator
                if not any(v != 0 for v in bar):
                    continue
                pat = _pattern(bar, length)
                for off, v in enumerate(pat):
                    T[(r, c - 1 - off)] = v
    else:
        r = idx
        top = sum(1 for rr in range(r) for cc in range(W) if g[rr][cc] != 0)
        bot = sum(1 for rr in range(r + 1, H) for cc in range(W) if g[rr][cc] != 0)
        if top >= bot:
            length = H - 1 - r
            for c in range(W):
                bar = [g[rr][c] for rr in range(r)][::-1]
                if not any(v != 0 for v in bar):
                    continue
                pat = _pattern(bar, length)
                for off, v in enumerate(pat):
                    T[(r + 1 + off, c)] = v
        else:
            length = r
            for c in range(W):
                bar = [g[rr][c] for rr in range(r + 1, H)]
                if not any(v != 0 for v in bar):
                    continue
                pat = _pattern(bar, length)
                for off, v in enumerate(pat):
                    T[(r - 1 - off, c)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
