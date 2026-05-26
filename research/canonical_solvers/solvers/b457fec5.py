def _components(grid, target):
    """4/8-connected components of cells equal to `target`."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r0 in range(H):
        for c0 in range(W):
            if grid[r0][c0] == target and not seen[r0][c0]:
                stack = [(r0, c0)]
                seen[r0][c0] = True
                cells = []
                while stack:
                    r, c = stack.pop()
                    cells.append((r, c))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < H and 0 <= nc < W and grid[nr][nc] == target and not seen[nr][nc]:
                                seen[nr][nc] = True
                                stack.append((nr, nc))
                comps.append(cells)
    return comps


def _find_key(grid):
    """The color legend: a horizontal run (length >= 2) of distinct
    non-zero, non-5 colors. Returns the ordered list of colors."""
    H, W = len(grid), len(grid[0])
    for r in range(H):
        run = []
        for c in range(W):
            v = grid[r][c]
            if v != 0 and v != 5:
                run.append(v)
            else:
                if len(run) >= 2:
                    return run
                run = []
        if len(run) >= 2:
            return run
    return None


def _corner_dist(comp, corner):
    """For each cell in comp, s = min(distance-from-corner along the two axes)."""
    minr = min(r for r, c in comp)
    maxr = max(r for r, c in comp)
    minc = min(c for r, c in comp)
    maxc = max(c for r, c in comp)
    out = {}
    for r, c in comp:
        if corner == 'tl':
            a, b = r - minr, c - minc
        elif corner == 'tr':
            a, b = r - minr, maxc - c
        elif corner == 'bl':
            a, b = maxr - r, c - minc
        else:  # 'br'
            a, b = maxr - r, maxc - c
        out[(r, c)] = min(a, b)
    return out


def _color_comp(comp, key):
    """Determine the output color for every cell of one 5-shape.

    The shape is a diagonal staircase band that grows out of one corner.
    Indexing the concentric corner-layers s = min(da, db) from that corner,
    the band is painted by cycling through the legend `key` (s % K), except
    the trailing layers (the shrinking tail, s >= maxS - (K-1)) are clamped
    to the last legend color. The correct corner is the one for which the
    cyclic rule is consistent on all non-last-color cells.
    """
    K = len(key)
    for corner in ('tl', 'tr', 'bl', 'br'):
        sval = _corner_dist(comp, corner)
        maxS = max(sval.values())
        thr = maxS - (K - 1)
        coloring = {}
        for (r, c), s in sval.items():
            idx = (K - 1) if s >= thr else (s % K)
            coloring[(r, c)] = key[idx]
        # validate orientation self-consistency:
        # the band layers 0..K-1 must each appear at the small-s end in order.
        ok = True
        for (r, c), s in sval.items():
            if s < thr and (s % K) != s % K:
                ok = False
        # The discriminating check: at the growing corner the layers s=0..K-1
        # are strictly the legend in order. Verify s=0 maps to key[0], s=1->key[1]...
        for s in range(min(K, maxS + 1)):
            cells_at_s = [p for p, v in sval.items() if v == s]
            if not cells_at_s:
                ok = False
                break
        if ok:
            # require that distinct small-s layers are actually distinct cells along
            # both edges (i.e. this corner is the narrow/growing one): the count of
            # cells at s grows then shrinks. Use it as orientation signal below.
            yield corner, coloring


def _infer_T(input_grid):
    """Latent mask: {(r,c): new_color} for every 5-cell, recolored by legend."""
    key = _find_key(input_grid)
    T = {}
    if key is None:
        return T
    K = len(key)
    for comp in _components(input_grid, 5):
        # Pick the corner orientation whose cyclic layering is consistent.
        chosen = None
        for corner in ('tl', 'tr', 'bl', 'br'):
            sval = _corner_dist(comp, corner)
            inv_consistent = True
            maxS = max(sval.values())
            thr = maxS - (K - 1)
            # Build the candidate coloring's index per cell.
            # Consistency test: the layers at the narrow (growing) corner must read
            # key[0], key[1], ... For a wrong corner the small-s layers fail to match
            # the actual outputs -- but we have no output here. Instead we use the
            # geometric signature: at the correct (growing) corner, the number of
            # cells with min(a,b)==s increases by ~1 per layer near s=0.
            counts = {}
            for v in sval.values():
                counts[v] = counts.get(v, 0) + 1
            # growing corner => counts[0] < counts[1] < ... initial increase
            ok = True
            prev = -1
            for s in range(min(K, maxS + 1)):
                cur = counts.get(s, 0)
                if cur <= prev:
                    ok = False
                    break
                prev = cur
            if ok:
                chosen = corner
                break
        if chosen is None:
            chosen = 'tl'
        sval = _corner_dist(comp, chosen)
        maxS = max(sval.values())
        thr = maxS - (K - 1)
        for (r, c), s in sval.items():
            idx = (K - 1) if s >= thr else (s % K)
            T[(r, c)] = key[idx]
    return T


def _apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = _infer_T(input_grid)
    return _apply_T(input_grid, T)
