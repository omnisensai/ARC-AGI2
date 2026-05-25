def infer_T(input_grid):
    """Latent mask: every maximal solid monochromatic rectangle of size >= 4x4
    (a uniform-color block embedded in the noisy field) is marked to be
    recolored to 4."""
    H, W = len(input_grid), len(input_grid[0])
    MIN = 4  # minimum height AND width of a solid block to recolor

    # Collect candidate solid monochromatic rectangles (>= MIN x MIN).
    candidates = []
    for color in range(10):
        b = [[1 if input_grid[r][c] == color else 0 for c in range(W)]
             for r in range(H)]
        for r0 in range(H):
            for c0 in range(W):
                if b[r0][c0] == 0:
                    continue
                curw = 0
                while c0 + curw < W and b[r0][c0 + curw] == 1:
                    curw += 1
                h = 0
                while r0 + h < H:
                    w2 = 0
                    while c0 + w2 < W and b[r0 + h][c0 + w2] == 1:
                        w2 += 1
                    curw = min(curw, w2)
                    if curw == 0:
                        break
                    h += 1
                    if h >= MIN and curw >= MIN:
                        candidates.append(
                            (color, r0, r0 + h - 1, c0, c0 + curw - 1))

    # Keep only maximal rectangles (drop those strictly contained by a larger
    # same-color rectangle in the candidate set).
    cset = set(candidates)
    maximal = []
    for rect in cset:
        co, ra, rb, ca, cb = rect
        area = (rb - ra + 1) * (cb - ca + 1)
        contained = False
        for o in cset:
            if o == rect:
                continue
            oco, ora, orb, oca, ocb = o
            if (oco == co and ora <= ra and orb >= rb and oca <= ca
                    and ocb >= cb
                    and (orb - ora + 1) * (ocb - oca + 1) > area):
                contained = True
                break
        if not contained:
            maximal.append(rect)

    # Build the latent transformation mask: solid blocks -> color 4.
    T = [[None] * W for _ in range(H)]
    for co, ra, rb, ca, cb in maximal:
        for r in range(ra, rb + 1):
            for c in range(ca, cb + 1):
                T[r][c] = 4
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
