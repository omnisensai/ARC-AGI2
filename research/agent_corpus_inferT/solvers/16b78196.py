"""Canonical latent-T solver for ARC puzzle 16b78196.

Rule (inferred from all train+test pairs):
  - The largest connected component is a "wall" band spanning one full grid
    dimension (full width -> horizontal wall, full height -> vertical wall).
  - The wall edge has concave "notches" (groups of background cells inside the
    band rectangle).  Each notch of size >= 2 anchors a stack of shapes.
  - Every other component is a small shape.  Shapes assemble into stacks that
    attach to the wall: one shape per stack pokes into the wall, exactly filling
    a notch (its band-facing edge matches the notch outline).  The remaining
    shapes nest outward, interlocking jigsaw-style (each placed at the tightest
    non-overlapping offset, sliding inward from outside the wall).
  - All shapes in a stack share the same size along the wall-parallel axis and
    are aligned to the same parallel position.  Their final ordering minimizes
    the total outward extent of the stack.
  - Original shape positions are cleared (set to background).

infer_T derives, from the input alone, a transformation mask (dict cell->color):
original shape cells -> 0, and all stacked/poked cells -> their shape colors.
apply_T copies the input and overwrites only masked cells.
"""

import itertools


def _comps(g, bg=0, diag=True):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    res = []
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diag:
        nb += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]
                st = [(r, c)]
                cells = []
                while st:
                    a, b = st.pop()
                    if 0 <= a < H and 0 <= b < W and not seen[a][b] and g[a][b] == col:
                        seen[a][b] = True
                        cells.append((a, b))
                        for dr, dc in nb:
                            st.append((a + dr, b + dc))
                res.append((col, cells))
    return res


def _group(cells):
    cells = set(cells)
    seen = set()
    res = []
    for x in cells:
        if x in seen:
            continue
        st = [x]
        grp = []
        while st:
            a = st.pop()
            if a in seen or a not in cells:
                continue
            seen.add(a)
            grp.append(a)
            r, c = a
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                st.append((r + dr, c + dc))
        res.append(frozenset(grp))
    return res


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])

    comps = _comps(g)
    comps.sort(key=lambda x: -len(x[1]))
    wall = set(comps[0][1])
    rsW = set(r for r, c in wall)
    csW = set(c for r, c in wall)
    horizontal = (len(csW) == W)
    lo, hi = (min(rsW), max(rsW)) if horizontal else (min(csW), max(csW))

    # background notches inside the band rectangle
    if horizontal:
        band_rect = set((r, c) for r in range(lo, hi + 1) for c in range(W))
    else:
        band_rect = set((r, c) for r in range(H) for c in range(lo, hi + 1))
    holes = set(x for x in band_rect if g[x[0]][x[1]] == 0)
    hgs = _group(holes)

    # normalized shapes
    shapes = []  # (color, norm_cells)
    orig_cells = set()
    for col, cells in comps[1:]:
        orig_cells |= set(cells)
        rr = [r for r, c in cells]
        cc = [c for r, c in cells]
        nr, nc = min(rr), min(cc)
        shapes.append((col, [(r - nr, c - nc) for r, c in cells]))

    def band_coord(x, y):
        return x if horizontal else y

    placements = []  # (color, set of abs cells)
    occ = set(wall)

    # for each shape, find every placement (straddling the wall) whose in-band
    # cells exactly fill a deep notch
    deep_notches = [h for h in hgs if len(h) >= 2]
    shape_notch = {}  # shape_idx -> list of (notch, abs_cells)
    for i, (col, norm) in enumerate(shapes):
        fills = []
        for dr in range(-H, H + 1):
            for dc in range(-W, W + 1):
                ab = [(r + dr, c + dc) for r, c in norm]
                if any(not (0 <= x < H and 0 <= y < W) for x, y in ab):
                    continue
                if any((x, y) in wall for x, y in ab):
                    continue
                inband = frozenset((x, y) for x, y in ab
                                   if lo <= band_coord(x, y) <= hi)
                if inband and inband in deep_notches:
                    fills.append((inband, frozenset(ab)))
        if fills:
            shape_notch[i] = fills

    # chains = distinct notches claimed by at least one shape
    notch_to_shapes = {}
    for i, fills in shape_notch.items():
        for notch, ab in fills:
            notch_to_shapes.setdefault(notch, []).append((i, ab))
    chain_notches = list(notch_to_shapes.keys())

    def outward_dir(ab):
        vals = [band_coord(x, y) for x, y in ab]
        below = sum(1 for v in vals if v > hi)
        above = sum(1 for v in vals if v < lo)
        return 1 if below >= above else -1

    def par_span(ab):
        ps = [y for x, y in ab] if horizontal else [x for x, y in ab]
        return min(ps), max(ps)

    def best_nest_with(d, pmin, pmax, ch_occ, gocc, norm):
        # slide a shape inward (from outside the wall) along the perpendicular
        # axis, keeping its parallel bbox aligned to [pmin..], until it touches
        # the chain without overlapping anything; return (outward_extent, cells)
        rr = [r for r, c in norm]
        cc = [c for r, c in norm]
        sh_par = (max(cc) + 1) if horizontal else (max(rr) + 1)
        if sh_par != (pmax - pmin + 1):
            return None
        par = pmin
        base_seq = range(H + W, -H - W - 1, -1) if d == 1 else range(-H - W, H + W + 1)
        pe = None
        pc = None
        pt = False
        for base in base_seq:
            if horizontal:
                absc = [(base + r, par + c) for r, c in norm]
            else:
                absc = [(par + r, base + c) for r, c in norm]
            if any(not (0 <= x < H and 0 <= y < W) for x, y in absc):
                if pt:
                    break
                pe = None; pc = None; pt = False
                continue
            if any((x, y) in gocc for x, y in absc):
                if pt:
                    break
                pe = None; pc = None; pt = False
                continue
            touch = any((x + a, y + b) in ch_occ for x, y in absc
                        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if horizontal:
                ext = max(x for x, y in absc) if d == 1 else -min(x for x, y in absc)
            else:
                ext = max(y for x, y in absc) if d == 1 else -min(y for x, y in absc)
            pe = ext; pc = frozenset(absc); pt = touch
        if pt:
            return pe, pc
        return None

    all_idx = list(range(len(shapes)))
    best_solution = [None]  # (total_extent, list of (color, abs_cells))

    seed_choices = [notch_to_shapes[n] for n in chain_notches]

    def solve_assign(seed_combo):
        used_seeds = [si for si, _ in seed_combo]
        if len(set(used_seeds)) != len(used_seeds):
            return
        chains = []
        gocc = set(occ)
        chain_notch = []
        for ci_seed, (si, ab) in enumerate(seed_combo):
            chains.append({'dir': outward_dir(ab),
                           'span': par_span(ab),
                           'occ': set(ab)})
            chain_notch.append(chain_notches[ci_seed])
            gocc |= ab
        rem = [j for j in all_idx if j not in used_seeds]

        def allowed_chains(j):
            if j in shape_notch:
                notches_j = set(n for n, _ in shape_notch[j])
                return [ci for ci in range(len(chains))
                        if chain_notch[ci] in notches_j]
            return list(range(len(chains)))

        local_best = [None]

        def rec(k, ch_occs, gocc2, plc, tot):
            if local_best[0] is not None and tot >= local_best[0][0]:
                return
            if k == len(rem):
                local_best[0] = (tot, list(plc))
                return
            j = rem[k]
            col, norm = shapes[j]
            for ci in allowed_chains(j):
                pmn, pmx = chains[ci]['span']
                bn = best_nest_with(chains[ci]['dir'], pmn, pmx,
                                    ch_occs[ci], gocc2, norm)
                if bn is None:
                    continue
                ext, absc = bn
                nco = list(ch_occs)
                nco[ci] = ch_occs[ci] | absc
                rec(k + 1, nco, gocc2 | absc, plc + [(col, absc)], tot + ext)

        init = [frozenset(ch['occ']) for ch in chains]
        rec(0, init, frozenset(gocc), [], 0)
        if local_best[0] is not None:
            total = local_best[0][0]
            plc = [(shapes[si][0], set(ab)) for si, ab in seed_combo] + \
                  [(col, set(ab)) for col, ab in local_best[0][1]]
            if best_solution[0] is None or total < best_solution[0][0]:
                best_solution[0] = (total, plc)

    for seed_combo in itertools.product(*seed_choices):
        solve_assign(list(seed_combo))

    if best_solution[0] is not None:
        for col, absc in best_solution[0][1]:
            placements.append((col, absc))

    # build latent transformation mask
    T = {}
    for x, y in orig_cells:
        T[(x, y)] = 0
    for col, cells in placements:
        for x, y in cells:
            T[(x, y)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
