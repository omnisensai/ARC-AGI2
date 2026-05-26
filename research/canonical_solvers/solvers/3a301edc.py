def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # bounding box of all non-background cells (the framed object)
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    if not cells:
        return {}
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)

    # outer color = the frame border; inner color = the center block
    inner = input_grid[(r0 + r1) // 2][(c0 + c1) // 2]

    # inner-color block bounding box (the contiguous block in the center)
    icells = [(r, c) for r, c in cells if input_grid[r][c] == inner]
    irs = [r for r, c in icells]
    ics = [c for r, c in icells]
    ih = max(irs) - min(irs) + 1
    iw = max(ics) - min(ics) + 1

    # ring thickness: for a square inner block this is just its side length;
    # for a rectangular block it shrinks by the aspect difference.
    ring = 2 * min(ih, iw) - max(ih, iw)

    # latent mask: paint a band of the inner color around the frame bbox of
    # thickness `ring`, only on background cells, clamped to grid bounds.
    T = {}
    R0, R1 = r0 - ring, r1 + ring
    C0, C1 = c0 - ring, c1 + ring
    for r in range(max(0, R0), min(H, R1 + 1)):
        for c in range(max(0, C0), min(W, C1 + 1)):
            if r0 <= r <= r1 and c0 <= c <= c1:
                continue  # inside the original frame bbox, leave untouched
            if input_grid[r][c] == bg:
                T[(r, c)] = inner
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
