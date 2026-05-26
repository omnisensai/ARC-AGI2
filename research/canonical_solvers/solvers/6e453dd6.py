from collections import deque


def infer_T(input_grid):
    """Infer the latent transformation mask.

    Structure: a vertical separator line (a full column of one non-6 color, here 5)
    splits the grid. To its left are shapes (connected components of color 0 on a 6
    background). Each shape is rigidly shifted right so its rightmost cell touches the
    column just left of the line. After shifting, any background hole that the shape
    encloses on its own and that lands in the interior column adjacent to the wall
    (lc-2) is "sealed" by the line; those rows get a 2-marker painted across the whole
    region right of the line.

    Returns a dict describing: the line column/color, the foreground color, the set of
    shifted shape cells, and the marked rows.
    """
    H = len(input_grid)
    W = len(input_grid[0])
    g = input_grid

    # locate the vertical separator: a full column of a single non-background color
    lc = None
    for c in range(W):
        col = [g[r][c] for r in range(H)]
        if all(v == col[0] for v in col) and col[0] != 6:
            lc = c
            break
    if lc is None:
        return {"line": None, "H": H, "W": W}

    sep = g[0][lc]
    fg = 0  # shape color

    # connected components of fg strictly left of the line (4-connectivity)
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(lc):
            if g[r][c] == fg and not seen[r][c]:
                q = deque([(r, c)])
                seen[r][c] = True
                cells = []
                while q:
                    cr, cc = q.popleft()
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < lc and g[nr][nc] == fg and not seen[nr][nc]:
                            seen[nr][nc] = True
                            q.append((nr, nc))
                comps.append(cells)

    def self_holes(cells):
        # background cells enclosed by this component's OWN cells (not using the line):
        # flood the complement of the shape within an expanded bounding box from its
        # border; anything not reached is an enclosed hole.
        cset = set(cells)
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        r0, r1, c0, c1 = min(rs) - 1, max(rs) + 1, min(cs) - 1, max(cs) + 1
        reach = set()
        q = deque()
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if (r == r0 or r == r1 or c == c0 or c == c1) and (r, c) not in cset:
                    reach.add((r, c))
                    q.append((r, c))
        while q:
            r, c = q.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if r0 <= nr <= r1 and c0 <= nc <= c1 and (nr, nc) not in cset and (nr, nc) not in reach:
                    reach.add((nr, nc))
                    q.append((nr, nc))
        holes = set()
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if (r, c) not in cset and (r, c) not in reach:
                    holes.add((r, c))
        return holes

    shifted = set()
    marks = set()
    for cells in comps:
        maxc = max(c for r, c in cells)
        shift = (lc - 1) - maxc  # push so rightmost cell sits at lc-1
        for r, c in cells:
            shifted.add((r, c + shift))
        for (hr, hc) in self_holes(cells):
            if hc + shift == lc - 2:  # hole sealed against the wall
                marks.add(hr)

    return {
        "line": lc,
        "sep": sep,
        "fg": fg,
        "shifted": shifted,
        "marks": sorted(marks),
        "H": H,
        "W": W,
    }


def apply_T(input_grid, T):
    H = T["H"]
    W = T["W"]
    lc = T["line"]
    if lc is None:
        return [row[:] for row in input_grid]
    out = [[6] * W for _ in range(H)]
    # keep the separator line and copy through the (background) right region
    for r in range(H):
        out[r][lc] = T["sep"]
        for c in range(lc + 1, W):
            out[r][c] = input_grid[r][c]
    # place the shifted shapes
    for (r, c) in T["shifted"]:
        out[r][c] = T["fg"]
    # paint 2-markers across the full right region on sealed-hole rows
    for r in T["marks"]:
        for c in range(lc + 1, W):
            out[r][c] = 2
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
