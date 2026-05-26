"""Canonical solver for ARC puzzle a09f6c25.

Rule: the grid holds a background color plus several shapes made of color 2.
Each shape is a connected component (8-connectivity). Single-cell components
are left untouched. For every multi-cell shape we test its bounding-box
mirror symmetries:
  - has a top-bottom (horizontal-axis) mirror only  -> recolor to 1
  - has a left-right (vertical-axis) mirror only     -> recolor to 3
  - has neither mirror symmetry                      -> recolor to 6
infer_T produces a {(r,c): color} mask; apply_T overwrites those cells.
"""


def _components(grid, fg):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == fg and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen:
                        continue
                    if not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if grid[rr][cc] != fg:
                        continue
                    seen.add((rr, cc))
                    comp.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((rr + dr, cc + dc))
                comps.append(comp)
    return comps


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most frequent color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # foreground color = the (single) non-background drawing color
    fgs = [v for v in counts if v != bg]
    T = {}
    if not fgs:
        return T
    fg = max(fgs, key=lambda v: counts[v])

    for comp in _components(input_grid, fg):
        if len(comp) <= 1:
            continue  # lone cells are left untouched
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        r0, c0 = min(rs), min(cs)
        h = max(rs) - r0 + 1
        w = max(cs) - c0 + 1
        norm = set((r - r0, c - c0) for r, c in comp)
        # left-right mirror (vertical axis of symmetry)
        lr_sym = all((r, w - 1 - c) in norm for r, c in norm)
        # top-bottom mirror (horizontal axis of symmetry)
        tb_sym = all((h - 1 - r, c) in norm for r, c in norm)
        if tb_sym and not lr_sym:
            color = 1
        elif lr_sym and not tb_sym:
            color = 3
        else:
            color = 6
        for cell in comp:
            T[cell] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
