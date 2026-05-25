import math


def _cells(grid):
    return {(r, c): grid[r][c]
            for r in range(len(grid))
            for c in range(len(grid[0])) if grid[r][c] != 0}


def _segment(a, b):
    """Cells of the straight/45-diagonal segment a..b, or None if not aligned."""
    (r0, c0), (r1, c1) = a, b
    dr, dc = r1 - r0, c1 - c0
    if dr == 0 and dc == 0:
        return [a]
    if dr == 0 or dc == 0 or abs(dr) == abs(dc):
        sr = (dr > 0) - (dr < 0)
        sc = (dc > 0) - (dc < 0)
        n = max(abs(dr), abs(dc))
        return [(r0 + i * sr, c0 + i * sc) for i in range(n + 1)]
    return None


def _connect(dots):
    """Connect-the-dots: outline by joining vertices around their centroid.

    For 2 dots, just the joining segment (if aligned). For >=3 dots, order
    them by polar angle about the centroid and connect consecutive vertices,
    which yields the polygon/diamond/frame outline rather than every chord.
    Only horizontal / vertical / 45-degree segments are drawn; unaligned
    pairs contribute nothing (isolated dots stay isolated).
    """
    dots = list(dots)
    out = set(dots)
    if len(dots) < 3:
        for i in range(len(dots)):
            for j in range(i + 1, len(dots)):
                s = _segment(dots[i], dots[j])
                if s:
                    out |= set(s)
        return out
    cr = sum(r for r, c in dots) / len(dots)
    cc = sum(c for r, c in dots) / len(dots)
    order = sorted(dots, key=lambda p: math.atan2(p[0] - cr, p[1] - cc))
    n = len(order)
    for i in range(n):
        s = _segment(order[i], order[(i + 1) % n])
        if s:
            out |= set(s)
    return out


def infer_T(input_grid):
    """Build the overwrite mask.

    Each color's cells are seed markers. Colors with >=2 seeds become a
    'connect-the-dots' outline (polygon edges along grid/diagonal lines).
    A color with a single seed is an 'outline' color: it duplicates the
    multi-seed shape it touches, translated so its seed lands on the nearest
    source seed, then erased where it would overlap the source shape -- i.e.
    a parallel copy hugging the source on the seed's side.
    """
    H, W = len(input_grid), len(input_grid[0])
    pts = _cells(input_grid)
    by_color = {}
    for k, v in pts.items():
        by_color.setdefault(v, []).append(k)

    singles = {c: ds[0] for c, ds in by_color.items() if len(ds) == 1}
    multis = {c: ds for c, ds in by_color.items() if len(ds) >= 2}
    shapes = {c: _connect(ds) for c, ds in multis.items()}

    T = {}

    # Multi-seed colors: draw their connect-the-dots outline.
    for color, shape in shapes.items():
        for (r, c) in shape:
            if 0 <= r < H and 0 <= c < W:
                T[(r, c)] = color

    # Single-seed colors: parallel copy of the adjacent multi-seed shape.
    for scolor, seed in singles.items():
        source = None
        for mcolor, shape in shapes.items():
            if any(max(abs(r - seed[0]), abs(c - seed[1])) <= 1
                   for (r, c) in shape):
                source = mcolor
                break
        if source is None:
            continue  # lone marker with no host shape: leave unchanged
        seeds = multis[source]
        anchor = min(seeds,
                     key=lambda d: max(abs(d[0] - seed[0]), abs(d[1] - seed[1])))
        off = (seed[0] - anchor[0], seed[1] - anchor[1])
        shape = shapes[source]
        copy = {(r + off[0], c + off[1]) for (r, c) in shape}
        for (r, c) in copy - shape:
            if 0 <= r < H and 0 <= c < W:
                T[(r, c)] = scolor

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
