def infer_T(input_grid):
    """Infer the latent transformation mask.

    The grid contains a rectangular frame drawn in color 5. Inside that frame
    there are exactly three colors: the global background (0) plus two other
    colors. The transformation swaps those two non-background colors within the
    frame interior; the background (0) and everything outside the frame stay.
    """
    H, W = len(input_grid), len(input_grid[0])
    FRAME = 5
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == FRAME]
    if not cells:
        return {}
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1 = min(rs) + 1, max(rs) - 1
    c0, c1 = min(cs) + 1, max(cs) - 1

    counts = {}
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            v = input_grid[r][c]
            if v == FRAME:
                continue
            counts[v] = counts.get(v, 0) + 1

    swap_colors = sorted(v for v in counts if v != 0)
    if len(swap_colors) != 2:
        return {}
    a, b = swap_colors
    mapping = {a: b, b: a}

    T = {}
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            v = input_grid[r][c]
            if v in mapping:
                T[(r, c)] = mapping[v]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
