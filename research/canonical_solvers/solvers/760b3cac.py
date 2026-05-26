def infer_T(input_grid):
    """Latent mask: reflect the 8-shape across the box edge toward which the
    4-arrow points, writing the mirrored copy into the adjacent column block."""
    g = input_grid
    H, W = len(g), len(g[0])
    cells8 = [(r, c) for r in range(H) for c in range(W) if g[r][c] == 8]
    cells4 = [(r, c) for r in range(H) for c in range(W) if g[r][c] == 4]
    T = {}
    if not cells8 or not cells4:
        return T

    # bounding box of the 8-shape
    r0 = min(r for r, c in cells8); r1 = max(r for r, c in cells8)
    c0 = min(c for r, c in cells8); c1 = max(c for r, c in cells8)
    bw = c1 - c0 + 1

    # arrow direction from the 4-shape: the protruding stem cell in its top row
    # sits on the left or right of the shape's center -> that's the side we copy to.
    fr0 = min(r for r, c in cells4)
    fc0 = min(c for r, c in cells4); fc1 = max(c for r, c in cells4)
    stem = [c for r, c in cells4 if r == fr0]
    fcenter = (fc0 + fc1) / 2.0
    stemc = sum(stem) / len(stem)
    right = stemc > fcenter

    # reflect the 8-shape across the box edge on the arrow side
    for r in range(r0, r1 + 1):
        for off in range(bw):  # distance into the new block from the box edge
            srcc = c1 - off if right else c0 + off  # nearest source col first
            val = g[r][srcc]
            tc = c1 + 1 + off if right else c0 - 1 - off
            if 0 <= tc < W:
                T[(r, tc)] = val
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
