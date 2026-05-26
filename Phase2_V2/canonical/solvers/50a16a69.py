"""Canonical solver for ARC puzzle 50a16a69.

Rule (single transformation):
  The input is a doubly-periodic tile pattern occupying the top-left block,
  with a solid border band (a single "marker" color) filling the bottom rows
  and right columns. The marker color is the only color that does NOT survive
  into the output.

  The transformation extends the periodic pattern across the ENTIRE grid
  (overwriting the marker band) AND shifts the whole pattern one column to the
  left, i.e. each output cell takes the pattern value of the cell immediately
  to its right:  out[r][c] = pattern_infinite[r][c+1].

infer_T computes, for every cell, the new color (the extended/shifted pattern
value), as a {(r,c): color} mask. apply_T copies the input and overwrites the
masked cells.
"""


def _marker_color(input_grid):
    """The marker (border) color is the input color that the pattern is NOT
    made of: it forms full bottom rows and/or full right columns. We detect it
    as a color that fills at least one complete row or complete column."""
    H, W = len(input_grid), len(input_grid[0])
    colors = set(v for row in input_grid for v in row)
    candidates = []
    for col in colors:
        full_row = any(all(input_grid[r][c] == col for c in range(W)) for r in range(H))
        full_col = any(all(input_grid[r][c] == col for r in range(H)) for c in range(W))
        if full_row or full_col:
            candidates.append(col)
    if not candidates:
        return None
    # Prefer the candidate occupying the contiguous bottom-right band: pick the
    # one with the fewest cells (the border) when several qualify.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return min(candidates, key=lambda c: counts[c])


def _period_vectors(pattern):
    """Find translation vectors under which the (partial) pattern is invariant.

    pattern: dict {(r,c): color} of the non-marker cells.
    Returns a list of small vectors (dr,dc) that preserve all overlapping cells.
    """
    cells = list(pattern.items())
    vecs = []
    for dr in range(-6, 7):
        for dc in range(0, 7):
            if dr == 0 and dc == 0:
                continue
            if dc == 0 and dr < 0:
                continue
            ok = True
            tested = 0
            for (r, c), v in cells:
                nb = pattern.get((r + dr, c + dc))
                if (r + dr, c + dc) in pattern:
                    tested += 1
                    if nb != v:
                        ok = False
                        break
            if ok and tested >= 3:
                vecs.append((dr, dc))
    return vecs


def _extend(pattern, vecs, rmin, rmax, cmin, cmax):
    """Propagate the periodic pattern to every cell in the requested range by
    walking the invariance vectors from known cells."""
    val = dict(pattern)
    changed = True
    while changed:
        changed = False
        for r in range(rmin, rmax):
            for c in range(cmin, cmax):
                if (r, c) in val:
                    continue
                got = False
                for (dr, dc) in vecs:
                    for s in (1, -1):
                        nr, nc = r + dr * s, c + dc * s
                        if (nr, nc) in val:
                            val[(r, c)] = val[(nr, nc)]
                            changed = True
                            got = True
                            break
                    if got:
                        break
    return val


def infer_T(input_grid):
    """Compute the latent transformation mask {(r,c): new_color}.

    new_color = infinite-pattern value one column to the right of (r,c).
    """
    H, W = len(input_grid), len(input_grid[0])
    marker = _marker_color(input_grid)

    # Pattern = all non-marker cells (the periodic tile region).
    if marker is None:
        pattern = {(r, c): input_grid[r][c] for r in range(H) for c in range(W)}
    else:
        pattern = {(r, c): input_grid[r][c]
                   for r in range(H) for c in range(W)
                   if input_grid[r][c] != marker}

    vecs = _period_vectors(pattern)
    # Extend one column beyond the right edge so we can read out[r][c]=pat[r][c+1].
    ext = _extend(pattern, vecs, -2, H + 2, -2, W + 2)

    T = {}
    for r in range(H):
        for c in range(W):
            if (r, c + 1) in ext:
                T[(r, c)] = ext[(r, c + 1)]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
