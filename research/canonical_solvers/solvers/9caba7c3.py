def infer_T(input_grid):
    """Infer the latent transformation mask.

    The grid has a background color (the most common, 5) mixed with 0s.
    Scattered fragments of color-2 cells each belong to a hidden 3x3 stamp.
    For every stamp we restore the full 3x3 box: the center becomes 4 and any
    ring cell that is not already a 2 becomes 7. The 2-cells stay as 2.

    The stamp center is the unique 3x3 placement that (a) contains all of the
    group's 2-cells in its ring, (b) has a background center, and (c) whose
    ring consists only of 2s and background (no 0s, no off-grid) -- i.e. the
    stamp sits on a clean background patch.
    """
    g = input_grid
    H, W = len(g), len(g[0])

    counts = {}
    for row in g:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)  # background = most common color

    # Group color-2 cells: any two 2-cells within Chebyshev distance 2 of each
    # other belong to the same 3x3 stamp (union-find).
    twos = [(r, c) for r in range(H) for c in range(W) if g[r][c] == 2]
    parent = list(range(len(twos)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(len(twos)):
        for j in range(i + 1, len(twos)):
            if max(abs(twos[i][0] - twos[j][0]),
                   abs(twos[i][1] - twos[j][1])) <= 2:
                parent[find(i)] = find(j)

    groups = {}
    for i, t in enumerate(twos):
        groups.setdefault(find(i), []).append(t)

    T = {}
    for grp in groups.values():
        gset = set(grp)
        r0 = min(r for r, c in grp); r1 = max(r for r, c in grp)
        c0 = min(c for r, c in grp); c1 = max(c for r, c in grp)

        # Choose the 3x3 center: among all placements whose 3x3 box covers the
        # whole group with a background center, pick the one whose ring is the
        # cleanest (fewest cells that are not 2 or background / off-grid).
        best = None
        best_score = None
        for cr in range(max(0, r1 - 1), min(H, r0 + 2)):
            for cc in range(max(0, c1 - 1), min(W, c0 + 2)):
                box = set((cr + dr, cc + dc)
                          for dr in (-1, 0, 1) for dc in (-1, 0, 1))
                if not all(t in box for t in grp):
                    continue
                if (cr, cc) in gset:  # center must be background, not a 2
                    continue
                ring = [(cr + dr, cc + dc)
                        for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                        if not (dr == 0 and dc == 0)]
                bad = sum(1 for (a, b) in ring
                          if not (0 <= a < H and 0 <= b < W)
                          or g[a][b] not in (2, bg))
                score = -bad
                if best_score is None or score > best_score:
                    best_score = score
                    best = (cr, cc)

        if best is None:
            continue

        cr, cc = best
        T[(cr, cc)] = 4
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, ccc = cr + dr, cc + dc
                if 0 <= rr < H and 0 <= ccc < W and g[rr][ccc] != 2:
                    T[(rr, ccc)] = 7
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
