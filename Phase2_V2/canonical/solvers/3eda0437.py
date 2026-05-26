def infer_T(input_grid):
    """Return a latent mask: a dict {(r,c): new_color} of cells to overwrite.

    Rule: locate the largest-area solid all-zero rectangle whose height and
    width are both >= 2 (a genuine 2D block, not a thin line), and mark every
    cell inside it to be recolored to 6.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    # Column-wise run heights of zeros ending at each cell, used for an
    # O(H*W^2) maximal all-zero rectangle scan.
    best = None  # (area, r0, r1, c0, c1)
    # zero_up[r][c] = number of consecutive zeros in column c ending at row r
    zero_up = [[0] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0:
                zero_up[r][c] = (zero_up[r - 1][c] + 1) if r > 0 else 1

    # For each bottom row r and each starting column c, extend a rectangle to
    # the right, tracking the limiting height (largest-rectangle-in-histogram
    # style, but enumerated directly to recover exact bounds).
    for r in range(H):
        for c0 in range(W):
            min_h = zero_up[r][c0]
            for c1 in range(c0, W):
                min_h = min(min_h, zero_up[r][c1])
                if min_h == 0:
                    break
                h = min_h
                w = c1 - c0 + 1
                if h < 2 or w < 2:
                    continue
                area = h * w
                r0 = r - h + 1
                cand = (area, r0, r, c0, c1)
                if best is None or area > best[0]:
                    best = cand

    T = {}
    if best is not None:
        _, r0, r1, c0, c1 = best
        for rr in range(r0, r1 + 1):
            for cc in range(c0, c1 + 1):
                T[(rr, cc)] = 6
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
