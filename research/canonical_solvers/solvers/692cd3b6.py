def infer_T(input_grid):
    """Infer the latent 4-fill mask connecting the two C-shaped boxes.

    Each shape is a 3x3 box of 2s with a 5 center and exactly one opening
    (a non-2 cell on its border). Every shape emits an L-shaped width-1 arm
    from its opening to a corner of a rectangle; the rectangle is the bounding
    box of the two claimed corners. Both arms and the rectangle are filled
    with 4.
    """
    g = input_grid
    H, W = len(g), len(g[0])

    # Locate the two shapes (centered on a 5) and their opening direction.
    shapes = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == 5:
                op = None
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if (dr, dc) != (0, 0):
                            rr, cc = r + dr, c + dc
                            if not (0 <= rr < H and 0 <= cc < W) or g[rr][cc] != 2:
                                op = (dr, dc)
                shapes.append({'cr': r, 'cc': c, 'r0': r - 1, 'r1': r + 1,
                               'c0': c - 1, 'c1': c + 1, 'op': op})

    if len(shapes) != 2 or any(s['op'] is None for s in shapes):
        return {}

    def corner_and_arm(S, O):
        dr, dc = S['op']
        cr, cc = S['cr'], S['cc']
        ocell = (cr + dr, cc + dc)  # the opening cell, just outside the center

        # Does the opening point toward the other shape (direct connect)?
        toward = (dr != 0 and ((dr > 0 and O['cr'] > cr) or (dr < 0 and O['cr'] < cr))) or \
                 (dc != 0 and ((dc > 0 and O['cc'] > cc) or (dc < 0 and O['cc'] < cc)))
        arm = set()
        if toward:
            # DIRECT: parallel edge just outside box, perpendicular = center line.
            if dr < 0:
                cor_r = S['r0'] - 1
            elif dr > 0:
                cor_r = S['r1'] + 1
            else:
                cor_r = cr
            if dc < 0:
                cor_c = S['c0'] - 1
            elif dc > 0:
                cor_c = S['c1'] + 1
            else:
                cor_c = cc
            corner = (cor_r, cor_c)
            rr, ccc = ocell
            while True:
                arm.add((rr, ccc))
                if (rr, ccc) == corner:
                    break
                rr += dr
                ccc += dc
        else:
            # WRAP: opening points away; arm exits then turns toward the gap.
            if dc != 0:  # horizontal opening, wraps vertically
                cor_c = S['c1'] + 1 if dc > 0 else S['c0'] - 1
                cor_r = S['r1'] + 1 if O['cr'] > cr else S['r0'] - 1
                corner = (cor_r, cor_c)
                ccc = cc + dc
                while True:
                    arm.add((cr, ccc))
                    if ccc == cor_c:
                        break
                    ccc += dc
                step = 1 if cor_r > cr else -1
                rr = cr
                while rr != cor_r:
                    rr += step
                    arm.add((rr, cor_c))
            else:  # vertical opening, wraps horizontally
                cor_r = S['r1'] + 1 if dr > 0 else S['r0'] - 1
                cor_c = S['c1'] + 1 if O['cc'] > cc else S['c0'] - 1
                corner = (cor_r, cor_c)
                rr = cr + dr
                while True:
                    arm.add((rr, cc))
                    if rr == cor_r:
                        break
                    rr += dr
                step = 1 if cor_c > cc else -1
                ccc = cc
                while ccc != cor_c:
                    ccc += step
                    arm.add((cor_r, ccc))
        return corner, arm

    A, B = shapes
    cA, armA = corner_and_arm(A, B)
    cB, armB = corner_and_arm(B, A)

    r0, r1 = min(cA[0], cB[0]), max(cA[0], cB[0])
    c0, c1 = min(cA[1], cB[1]), max(cA[1], cB[1])

    T = {}
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            T[(r, c)] = 4
    for cell in armA | armB:
        T[cell] = 4
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H, W = len(out), len(out[0])
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
