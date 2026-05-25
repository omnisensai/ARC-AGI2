def _perimeter_coords(H, W):
    """Clockwise ordering of border cells, starting at the top-left corner."""
    coords = []
    for c in range(W):
        coords.append((0, c))
    for r in range(1, H):
        coords.append((r, W - 1))
    for c in range(W - 2, -1, -1):
        coords.append((H - 1, c))
    for r in range(H - 2, 0, -1):
        coords.append((r, 0))
    return coords


def infer_T(input_grid):
    """Infer the latent mask {(r,c): color}.

    A single connected marker sits on the grid border. Unrolling the border
    into a 1D cyclic path, the marker occupies a contiguous run of length
    `span`. It is stamped repeatedly around the border with period 2*span
    (the run followed by an equal-length background gap), keeping its original
    placement. Only border cells that become the marker color are masked.
    """
    H, W = len(input_grid), len(input_grid[0])

    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    per = _perimeter_coords(H, W)
    L = len(per)
    line = [input_grid[r][c] for (r, c) in per]

    # marker color (any non-background border cell)
    color = next((v for v in line if v != bg), None)
    T = {}
    if color is None:
        return T

    marked = set(i for i in range(L) if line[i] != bg)
    if not marked:
        return T

    # find the (single) contiguous cyclic run: a start index whose
    # predecessor on the cycle is background
    starts = [i for i in marked if (i - 1) % L not in marked]
    start = starts[0]

    # measure the run length (span)
    span = 0
    j = start
    while (j % L) in marked and span < L:
        span += 1
        j += 1

    period = 2 * span
    if period <= 0:
        return T

    # stamp the run repeatedly around the perimeter at the original phase
    for off in range(0, L, period):
        for k in range(span):
            pos = (start + off + k) % L
            r, c = per[pos]
            T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
