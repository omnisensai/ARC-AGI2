def infer_T(input_grid):
    """Reflect the color-2 shape across the two axes defined by the 3-block.

    A small 2x2 (or rectangular) block of color 3 acts as a pivot. The single
    color-2 shape sits in one quadrant relative to that block. The latent mask
    paints three mirrored copies of that shape (horizontal, vertical, and
    point reflection) using the 3-block's bounding-box center as the axes.
    """
    H, W = len(input_grid), len(input_grid[0])
    threes = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 3]
    twos = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 2]
    T = {}
    if not threes or not twos:
        return T
    r3min = min(r for r, c in threes); r3max = max(r for r, c in threes)
    c3min = min(c for r, c in threes); c3max = max(c for r, c in threes)
    # doubled mirror centers: cell r maps to (raxis - r), col c maps to (caxis - c)
    raxis = r3min + r3max
    caxis = c3min + c3max
    for (r, c) in twos:
        rr = raxis - r
        cc = caxis - c
        for (nr, nc) in ((r, cc), (rr, c), (rr, cc)):
            if 0 <= nr < H and 0 <= nc < W:
                T[(nr, nc)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
