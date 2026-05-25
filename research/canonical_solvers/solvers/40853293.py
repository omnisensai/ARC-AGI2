def infer_T(input_grid):
    """Infer the latent mask {(r,c): color}.

    The grid contains pairs of same-colored, non-background marker cells. Each
    color appears exactly twice, aligned in a shared row or shared column. Each
    pair is connected by an inclusive straight segment of that color. Where a
    horizontal segment and a vertical segment cross, the vertical segment wins.
    """
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    pts = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg:
                pts.setdefault(v, []).append((r, c))

    horizontals = []  # (color, row, c0, c1)
    verticals = []    # (color, col, r0, r1)
    for color, ps in pts.items():
        if len(ps) != 2:
            continue
        (r0, c0), (r1, c1) = ps
        if r0 == r1:
            horizontals.append((color, r0, min(c0, c1), max(c0, c1)))
        elif c0 == c1:
            verticals.append((color, c0, min(r0, r1), max(r0, r1)))

    T = {}
    # Draw horizontals first, then verticals so verticals overwrite crossings.
    for color, r, ca, cb in horizontals:
        for c in range(ca, cb + 1):
            T[(r, c)] = color
    for color, c, ra, rb in verticals:
        for r in range(ra, rb + 1):
            T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
