def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    g = input_grid

    # placeholder region (color 3) marks where missing shapes belong
    threes = [(r, c) for r in range(H) for c in range(W) if g[r][c] == 3]

    # rows/cols containing the shape color (2)
    twos = [(r, c) for r in range(H) for c in range(W) if g[r][c] == 2]
    rows_with2 = sorted(set(r for r, c in twos))
    cols_with2 = sorted(set(c for r, c in twos))

    # group consecutive indices into bands (gaps are empty lines)
    def bands(idxs):
        bs, cur = [], [idxs[0]]
        for x in idxs[1:]:
            if x == cur[-1] + 1:
                cur.append(x)
            else:
                bs.append(cur)
                cur = [x]
        bs.append(cur)
        return bs

    rbands = bands(rows_with2)
    cbands = bands(cols_with2)
    sh = max(len(b) for b in rbands)   # shape height
    sw = max(len(b) for b in cbands)   # shape width
    step_r = sh + 1                    # slot pitch (shape + 1 gap)
    step_c = sw + 1
    org_r = min(b[0] for b in rbands)  # lattice origin
    org_c = min(b[0] for b in cbands)

    n_mr = (H - org_r + step_r - 1) // step_r
    n_mc = (W - org_c + step_c - 1) // step_c

    # read each meta-slot block: which (dr,dc) cells hold a 2
    slots = {}
    for mi in range(n_mr):
        for mj in range(n_mc):
            br, bc = org_r + mi * step_r, org_c + mj * step_c
            cells = set()
            for dr in range(sh):
                for dc in range(sw):
                    r, c = br + dr, bc + dc
                    if 0 <= r < H and 0 <= c < W and g[r][c] == 2:
                        cells.add((dr, dc))
            slots[(mi, mj)] = cells

    # canonical shape = the fullest slot pattern
    canon = set()
    for cells in slots.values():
        if len(cells) > len(canon):
            canon = cells
    canon_sorted = sorted(canon)

    # meta-slots that hold a complete shape
    present = set(mij for mij, cells in slots.items() if cells == canon)

    # the meta-grid mirrors the shape: occupied meta-slots == cells of the shape.
    # any canon cell with no shape present is "missing" (hidden under 3-region).
    canon_meta = set(canon_sorted)
    missing = [cell for cell in canon_sorted if cell not in present]

    T = {}

    # 1) erase the placeholder region
    for r, c in threes:
        T[(r, c)] = 0

    # 2) draw every missing shape into its meta-slot
    all_shape_slots = set(present)
    for (mi, mj) in missing:
        br, bc = org_r + mi * step_r, org_c + mj * step_c
        for (dr, dc) in canon_sorted:
            T[(br + dr, bc + dc)] = 2
        all_shape_slots.add((mi, mj))

    # 3) mark one cell of each shape with 8: shape at meta-slot (mi,mj) gets the
    #    cell whose normalized coord equals (mi,mj).
    for (mi, mj) in all_shape_slots:
        if (mi, mj) in canon_meta:
            br, bc = org_r + mi * step_r, org_c + mj * step_c
            T[(br + mi, bc + mj)] = 8

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out
