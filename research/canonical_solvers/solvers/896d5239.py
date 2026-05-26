"""Canonical latent-T solver for ARC puzzle 896d5239.

Rule: the grid contains chevron/arrow shapes drawn in color 3. Each chevron is a
right-isosceles triangle whose two slanted edges (arms) emanate from an apex in
two perpendicular diagonal directions; the base edge (connecting the two arm
tips) is not drawn. The transformation fills the interior of each triangle with
color 8, growing as a symmetric cone from the apex outward in the opening
direction up to the arm length, leaving the existing 3-cells untouched.

infer_T detects every chevron from the 3-cells alone:
  - connected (8-diagonal) runs of 3s -> apex is the bend cell (the 3-cell whose
    two diagonal 3-neighbors are perpendicular); arm length = longest contiguous
    diagonal run of 3s from the apex.
  - isolated triples of 3s (only the three vertices drawn) -> apex is the vertex
    from which the other two lie on perpendicular diagonals at equal distance.

apply_T copies the input and overwrites only the masked cone cells with 8.
"""

DIAGS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def _perp(d1, d2):
    return d1[0] * d2[0] + d1[1] * d2[1] == 0 and d1 != d2


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    threes = set((r, c) for r in range(H) for c in range(W)
                 if input_grid[r][c] == 3)

    # 8-diagonal connected components of 3-cells
    seen, comps = set(), []
    for s in threes:
        if s in seen:
            continue
        stack, comp = [s], []
        while stack:
            r, c = stack.pop()
            if (r, c) in seen or (r, c) not in threes:
                continue
            seen.add((r, c))
            comp.append((r, c))
            for dr, dc in DIAGS:
                stack.append((r + dr, c + dc))
        comps.append(comp)

    chevrons = []   # (apex, dirA, dirB, length)
    used = set()

    # connected chevrons: apex = bend cell, length = longest contiguous arm
    for comp in comps:
        if len(comp) < 2:
            continue
        cs = set(comp)
        apex = dirs = None
        for (r, c) in comp:
            nb = [d for d in DIAGS if (r + d[0], c + d[1]) in cs]
            for i in range(len(nb)):
                for j in range(i + 1, len(nb)):
                    if _perp(nb[i], nb[j]):
                        apex, dirs = (r, c), (nb[i], nb[j])
                        break
                if apex:
                    break
            if apex:
                break
        if not apex:
            continue
        ar, ac = apex

        def contig(dd):
            k = 0
            while (ar + dd[0] * (k + 1), ac + dd[1] * (k + 1)) in threes:
                k += 1
            return k

        length = max(contig(dirs[0]), contig(dirs[1]))
        chevrons.append((apex, dirs[0], dirs[1], length))
        for x in comp:
            used.add(x)

    # isolated triples: only the three triangle vertices are drawn
    remset = set(t for t in threes if t not in used)
    for apex in list(remset):
        if apex not in remset:
            continue
        ar, ac = apex
        found = None
        for i in range(len(DIAGS)):
            for j in range(i + 1, len(DIAGS)):
                d1, d2 = DIAGS[i], DIAGS[j]
                if not _perp(d1, d2):
                    continue
                for k in range(1, max(H, W)):
                    p1 = (ar + d1[0] * k, ac + d1[1] * k)
                    p2 = (ar + d2[0] * k, ac + d2[1] * k)
                    if p1 in remset and p2 in remset:
                        found = (d1, d2, k)
                        break
                if found:
                    break
            if found:
                break
        if found:
            d1, d2, k = found
            chevrons.append((apex, d1, d2, k))
            remset.discard(apex)
            remset.discard((ar + d1[0] * k, ac + d1[1] * k))
            remset.discard((ar + d2[0] * k, ac + d2[1] * k))

    # Build the latent mask: cells that become 8.
    T = set()
    for (apex, dA, dB, length) in chevrons:
        ar, ac = apex
        odr, odc = dA[0] + dB[0], dA[1] + dB[1]   # opening (cardinal) direction
        if odr:
            odr //= abs(odr)
        if odc:
            odc //= abs(odc)
        for k in range(0, length + 1):
            cr, cc = ar + odr * k, ac + odc * k
            for t in range(-k, k + 1):
                if odr == 0:        # opening horizontal -> vertical cross-slice
                    rr, cc2 = cr + t, cc
                else:               # opening vertical -> horizontal cross-slice
                    rr, cc2 = cr, cc + t
                if 0 <= rr < H and 0 <= cc2 < W and input_grid[rr][cc2] != 3:
                    T.add((rr, cc2))
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c) in T:
        out[r][c] = 8
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
