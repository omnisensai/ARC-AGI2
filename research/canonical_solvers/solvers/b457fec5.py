def _components(grid, target):
    """8-connected components of cells equal to `target`."""
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


def _reference_corner(comp):
    """The recoloring grows out of one corner of the parallelogram.

    A staircase parallelogram touches exactly two opposite corners of its
    bounding box. The reference (growing-tip) corner is the upper one
    (smaller row)."""
    cset = set(comp)
    minr = min(r for r, c in comp)
    maxr = max(r for r, c in comp)
    minc = min(c for r, c in comp)
    maxc = max(c for r, c in comp)
    candidates = []
    if (minr, minc) in cset:
        candidates.append(('tl', minr, minc))
    if (minr, maxc) in cset:
        candidates.append(('tr', minr, maxc))
    if (maxr, minc) in cset:
        candidates.append(('bl', maxr, minc))
    if (maxr, maxc) in cset:
        candidates.append(('br', maxr, maxc))
    if not candidates:
        return 'tl'
    # upper-most (smallest row); tie-break smallest col.
    candidates.sort(key=lambda x: (x[1], x[2]))
    return candidates[0][0]


def _infer_T(input_grid):
    """Latent mask: {(r,c): new_color} for every 5-cell, recolored by legend.

    Each 5-shape is a diagonal staircase band growing from its top corner.
    Indexing concentric corner-layers s = min(da, db) from that corner, the
    band is painted cycling through the legend `key` (key[s % K]); the trailing
    layers (the shrinking tail, s >= maxS - (K-1)) clamp to the last legend
    color."""
    key = _find_key(input_grid)
    T = {}
    if key is None:
        return T
    K = len(key)
    for comp in _components(input_grid, 5):
        corner = _reference_corner(comp)
        sval = _corner_dist(comp, corner)
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
