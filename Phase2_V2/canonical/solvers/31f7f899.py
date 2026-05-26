from collections import Counter


def _axis_and_bg(grid):
    """Find the background colour and the 6-line (row or column of 6s)."""
    H, W = len(grid), len(grid[0])
    cnt = Counter(v for row in grid for v in row)
    bg = cnt.most_common(1)[0][0]
    for r in range(H):
        if sum(1 for c in range(W) if grid[r][c] == 6) >= 2:
            return bg, 'row', r
    for c in range(W):
        if sum(1 for r in range(H) if grid[r][c] == 6) >= 2:
            return bg, 'col', c
    return bg, None, None


def _components(grid, bg):
    """4-connected single-colour components, excluding bg and the axis colour 6."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v in (bg, 6) or (r, c) in seen:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                rr, cc = stack.pop()
                if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W):
                    continue
                if grid[rr][cc] != v:
                    continue
                seen.add((rr, cc))
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((rr + dr, cc + dc))
            rs = [x[0] for x in cells]
            cs = [x[1] for x in cells]
            comps.append({
                'color': v,
                'rmin': min(rs), 'rmax': max(rs),
                'cmin': min(cs), 'cmax': max(cs),
            })
    return comps


def infer_T(input_grid):
    """Build the latent overwrite mask.

    Each component is a bar perpendicular to the 6-axis, crossing it.  The bars
    keep their colour and their position/thickness ALONG the axis, but their
    extents ACROSS the axis are reassigned: the multiset of perpendicular spans
    (their offsets relative to the axis line) is sorted by length and handed out
    to the bars in order of their position along the axis (ascending).
    """
    H, W = len(input_grid), len(input_grid[0])
    bg, orient, axis = _axis_and_bg(input_grid)
    T = {}
    if orient is None:
        return T, bg
    comps = _components(input_grid, bg)
    if not comps:
        return T, bg

    if orient == 'row':
        # position along axis = column; span across axis = rows
        comps.sort(key=lambda b: b['cmin'])
        spans = sorted(((b['rmin'] - axis, b['rmax'] - axis) for b in comps),
                       key=lambda s: s[1] - s[0])
        # clear all existing bar cells
        for b in comps:
            for r in range(b['rmin'], b['rmax'] + 1):
                for c in range(b['cmin'], b['cmax'] + 1):
                    if input_grid[r][c] == b['color']:
                        T[(r, c)] = bg
        # repaint with reassigned spans, preserving offsets relative to axis
        for b, (lo, hi) in zip(comps, spans):
            for d in range(lo, hi + 1):
                r = axis + d
                if 0 <= r < H:
                    for c in range(b['cmin'], b['cmax'] + 1):
                        T[(r, c)] = b['color']
    else:
        # position along axis = row; span across axis = columns
        comps.sort(key=lambda b: b['rmin'])
        spans = sorted(((b['cmin'] - axis, b['cmax'] - axis) for b in comps),
                       key=lambda s: s[1] - s[0])
        for b in comps:
            for r in range(b['rmin'], b['rmax'] + 1):
                for c in range(b['cmin'], b['cmax'] + 1):
                    if input_grid[r][c] == b['color']:
                        T[(r, c)] = bg
        for b, (lo, hi) in zip(comps, spans):
            for d in range(lo, hi + 1):
                c = axis + d
                if 0 <= c < W:
                    for r in range(b['rmin'], b['rmax'] + 1):
                        T[(r, c)] = b['color']
    return T, bg


def apply_T(input_grid, T_bg):
    T, _bg = T_bg
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
