def comps(g, color):
    """8-connected components of `color` in grid g."""
    H, W = len(g), len(g[0])
    seen = set(); out = []
    dirs = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr or dc)]
    for r in range(H):
        for c in range(W):
            if g[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]; comp = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if g[rr][cc] != color:
                        continue
                    seen.add((rr, cc)); comp.append((rr, cc))
                    for dr, dc in dirs:
                        stack.append((rr + dr, cc + dc))
                out.append(comp)
    return out


def group_markers(cells):
    """Cluster isolated 4-marker cells (spaced 2 apart) into L-frame groups."""
    cells = set(cells); seen = set(); groups = []
    for cell in list(cells):
        if cell in seen:
            continue
        stack = [cell]; grp = []
        while stack:
            x = stack.pop()
            if x in seen or x not in cells:
                continue
            seen.add(x); grp.append(x); r, c = x
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    n = (r + dr, c + dc)
                    if n in cells and n not in seen:
                        stack.append(n)
        groups.append(sorted(grp))
    return groups


def analyze_frame(grp):
    """An L-frame is 3 markers: a corner sharing a row with one and a col with
    the other. Return (corner, horizontal-arm-end, vertical-arm-end)."""
    if len(grp) != 3:
        return None
    for r, c in grp:
        sr = [x for x in grp if x[0] == r and x != (r, c)]
        sc = [x for x in grp if x[1] == c and x != (r, c)]
        if sr and sc:
            return (r, c), sr[0], sc[0]
    return None


def is_hollow_ring(rel):
    """True if normalized cell set is exactly the perimeter of its >=3x3 bbox."""
    s = set(rel)
    h = max(r for r, c in rel) + 1
    w = max(c for r, c in rel) + 1
    if h < 3 or w < 3:
        return False
    perim = set((r, c) for r in range(h) for c in range(w)
                if r in (0, h - 1) or c in (0, w - 1))
    return s == perim


def infer_T(g):
    """Latent mask {(r,c): new_color}.

    Structure: scattered groups of three 4-cells form L-shaped frames (a corner
    plus two arms reaching 2 cells out). A single 2-coloured motif sits inside
    one frame (the source). Read the motif relative to that frame's corner,
    normalising the two arm directions to positive (a dihedral de-flip). For a
    hollow rectangular ring motif, drop the two perimeter cells flanking the box
    corner diagonally opposite the marker corner. Then stamp the (flipped) motif
    into every frame; at frames where the motif overwrites pre-existing 2-cells
    those extra cells are cleared to background.
    """
    H, W = len(g), len(g[0])
    cells4 = [c[0] for c in comps(g, 4)]
    frames = []
    for grp in group_markers(cells4):
        fr = analyze_frame(grp)
        if fr:
            frames.append(fr)
    tcomp = comps(g, 2)
    T = {}
    if not tcomp or not frames:
        return T
    tcomp = tcomp[0]

    # source frame = the one whose corner is closest to the motif centroid
    tcen = (sum(r for r, c in tcomp) / len(tcomp),
            sum(c for r, c in tcomp) / len(tcomp))
    best = None; bd = 1e9
    for fr in frames:
        corner = fr[0]
        d = abs(corner[0] - tcen[0]) + abs(corner[1] - tcen[1])
        if d < bd:
            bd = d; best = fr
    scorner, sharm, svarm = best
    sdh = 1 if sharm[1] > scorner[1] else -1
    sdv = 1 if svarm[0] > scorner[0] else -1

    # canonical (de-flipped) motif relative to the marker corner -> normalize
    motif = set(((r - scorner[0]) * sdv, (c - scorner[1]) * sdh) for r, c in tcomp)
    mr = min(r for r, c in motif); mc = min(c for r, c in motif)
    loc = set((r - mr, c - mc) for r, c in motif)
    full_loc = set(loc)
    if is_hollow_ring(loc):
        h = max(r for r, c in loc) + 1
        w = max(c for r, c in loc) + 1
        far = (h - 1, w - 1)            # corner diagonally opposite marker corner
        loc = loc - {(far[0] - 1, far[1]), (far[0], far[1] - 1)}
    motif = set((r + mr, c + mc) for r, c in loc)
    footprint = set((r + mr, c + mc) for r, c in full_loc)
    cleared = footprint - motif

    for fr in frames:
        corner, harm, varm = fr
        cr, cc = corner
        dh = 1 if harm[1] > cc else -1
        dv = 1 if varm[0] > cr else -1
        for gr, gc in motif:
            R = cr + dv * gr; C = cc + dh * gc
            if 0 <= R < H and 0 <= C < W:
                T[(R, C)] = 2
        for gr, gc in cleared:
            R = cr + dv * gr; C = cc + dh * gc
            if 0 <= R < H and 0 <= C < W and (R, C) not in T:
                T[(R, C)] = 0
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
