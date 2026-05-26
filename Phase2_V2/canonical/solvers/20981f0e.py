def _components(cells):
    """8-connected components of a set of (r,c) cells."""
    cells = set(cells)
    seen = set()
    out = []
    for start in cells:
        if start in seen:
            continue
        stack = [start]
        comp = []
        while stack:
            r, c = stack.pop()
            if (r, c) in seen or (r, c) not in cells:
                continue
            seen.add((r, c))
            comp.append((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr or dc:
                        stack.append((r + dr, c + dc))
        out.append(comp)
    return out


def infer_T(input_grid):
    """
    Latent transformation mask.

    Structure: cells of color 2 form a lattice (intersections of fixed rows and
    columns). Each connected component of color-1 cells sits inside one lattice
    cell, defined by the nearest 2 above-and-left of it (largest r2 <= shape's
    min row, largest c2 <= shape's min col). Each shape is translated so its
    bounding-box top-left lands at (r2 + 2, c2 + 2).

    T = dict {(r, c): new_color} giving the cells whose value changes: the moved
    1-cells become 1, and the vacated original 1-cells become background.
    """
    H, W = len(input_grid), len(input_grid[0])

    rows2 = sorted({r for r in range(H) for c in range(W) if input_grid[r][c] == 2})
    cols2 = sorted({c for r in range(H) for c in range(W) if input_grid[r][c] == 2})

    ones = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 1]
    comps = _components(ones)

    T = {}
    # Vacate every original 1 cell (background = 0).
    for (r, c) in ones:
        T[(r, c)] = 0

    # Place each shape at its lattice-anchored target position.
    for comp in comps:
        minr = min(r for r, _ in comp)
        minc = min(c for _, c in comp)
        cand_r = [r for r in rows2 if r <= minr]
        cand_c = [c for c in cols2 if c <= minc]
        if not cand_r or not cand_c:
            # No anchoring lattice point: leave shape in place.
            for (r, c) in comp:
                T[(r, c)] = 1
            continue
        r2 = max(cand_r)
        c2 = max(cand_c)
        dr = (r2 + 2) - minr
        dc = (c2 + 2) - minc
        for (r, c) in comp:
            T[(r + dr, c + dc)] = 1

    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
