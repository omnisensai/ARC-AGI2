def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    nonbg = [c for c in counts if c != bg]

    # Identify the rectangle frame: a color whose bounding-box perimeter is fully
    # that color (a hollow rectangle outline).
    border_color = None
    interior_bbox = None
    for c in nonbg:
        cells = [(r, cc) for r in range(H) for cc in range(W) if input_grid[r][cc] == c]
        if not cells:
            continue
        r0 = min(p[0] for p in cells); r1 = max(p[0] for p in cells)
        c0 = min(p[1] for p in cells); c1 = max(p[1] for p in cells)
        perim_ok = True
        for cc in range(c0, c1 + 1):
            if input_grid[r0][cc] != c or input_grid[r1][cc] != c:
                perim_ok = False; break
        if perim_ok:
            for r in range(r0, r1 + 1):
                if input_grid[r][c0] != c or input_grid[r][c1] != c:
                    perim_ok = False; break
        if perim_ok and (r1 - r0) >= 2 and (c1 - c0) >= 2:
            border_color = c
            interior_bbox = (r0 + 1, r1 - 1, c0 + 1, c1 - 1)
            break

    T = [[None] * W for _ in range(H)]
    if border_color is None or interior_bbox is None:
        return T

    ir0, ir1, ic0, ic1 = interior_bbox
    # Marker cells inside the frame interior (anything not background or border).
    marker_cells = [(r, c) for r in range(ir0, ir1 + 1) for c in range(ic0, ic1 + 1)
                    if input_grid[r][c] not in (bg, border_color)]
    if not marker_cells:
        return T
    mr0 = min(p[0] for p in marker_cells); mr1 = max(p[0] for p in marker_cells)
    mc0 = min(p[1] for p in marker_cells); mc1 = max(p[1] for p in marker_cells)

    # Fill the interior with the border color, but preserve the marker bounding box.
    for r in range(ir0, ir1 + 1):
        for c in range(ic0, ic1 + 1):
            inside = (mr0 <= r <= mr1 and mc0 <= c <= mc1)
            if not inside and input_grid[r][c] != border_color:
                T[r][c] = border_color
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
