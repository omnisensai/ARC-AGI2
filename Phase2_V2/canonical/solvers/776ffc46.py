def _components(grid, colorpred):
    """8-connected components of cells whose value satisfies colorpred."""
    H, W = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if (r, c) in seen or not colorpred(grid[r][c]):
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                rr, cc = stack.pop()
                if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W):
                    continue
                if not colorpred(grid[rr][cc]):
                    continue
                seen.add((rr, cc))
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr or dc:
                            stack.append((rr + dr, cc + dc))
            out.append(cells)
    return out


def _norm(cells):
    """Translate a cell set so its bounding box starts at (0,0)."""
    mr = min(r for r, c in cells)
    mc = min(c for r, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _key_color(grid):
    """The single content color: not background(0), not marker(1), not frame(5)."""
    for row in grid:
        for v in row:
            if v not in (0, 1, 5):
                return v
    return None


def _closed_box_templates(grid, key):
    """Normalized shapes of the key-colored content inside fully-closed 5-frames."""
    H, W = len(grid), len(grid[0])
    templates = set()
    for frame in _components(grid, lambda v: v == 5):
        rs = [r for r, c in frame]
        cs = [c for r, c in frame]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        if r1 - r0 < 2 or c1 - c0 < 2:
            continue
        cset = set(frame)
        # require a complete rectangular border
        full = all((r0, c) in cset and (r1, c) in cset for c in range(c0, c1 + 1))
        if full:
            full = all((r, c0) in cset and (r, c1) in cset for r in range(r0, r1 + 1))
        if not full:
            continue
        interior = [(r, c) for r in range(r0 + 1, r1)
                    for c in range(c0 + 1, c1) if grid[r][c] == key]
        if interior:
            templates.add(_norm(interior))
    return templates


def infer_T(input_grid):
    """Latent mask {(r,c): new_color}: recolor every 1-component whose exact
    shape matches a key-template (the content inside a closed 5-frame)."""
    key = _key_color(input_grid)
    T = {}
    if key is None:
        return T
    templates = _closed_box_templates(input_grid, key)
    for comp in _components(input_grid, lambda v: v == 1):
        if _norm(comp) in templates:
            for (r, c) in comp:
                T[(r, c)] = key
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
