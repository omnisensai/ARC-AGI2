def infer_T(input_grid):
    """Infer the latent transformation mask {(r,c): color}.

    Structure: the input contains a single 2x2 block of non-zero cells. Some of
    its corners hold the marker color 2; the remaining corners hold a single
    fill color C. Each marker corner emits a 3-wide diagonal ray: the 2x2
    footprint (painted entirely with C) is stamped repeatedly, stepping outward
    in that corner's diagonal direction until it leaves the grid.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Bounding box of the non-zero cells = the 2x2 block.
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != 0]
    if not cells:
        return {}
    r0 = min(r for r, c in cells)
    c0 = min(c for r, c in cells)

    block = {(dr, dc): input_grid[r0 + dr][c0 + dc] for dr in (0, 1) for dc in (0, 1)}
    marker = 2
    fills = [v for v in block.values() if v != marker]
    if not fills:
        return {}
    fill = fills[0]
    marker_corners = [k for k, v in block.items() if v == marker]

    T = {}
    for (cr, cc) in marker_corners:
        dr = 1 if cr == 1 else -1   # outward diagonal direction (rows)
        dc = 1 if cc == 1 else -1   # outward diagonal direction (cols)
        # Stamp the full 2x2 footprint along the diagonal.
        k = 0
        while True:
            or_, oc_ = r0 + k * dr, c0 + k * dc
            footprint = [(or_ + dd, oc_ + ee) for dd in (0, 1) for ee in (0, 1)]
            if all(not (0 <= rr < H and 0 <= cc2 < W) for rr, cc2 in footprint):
                break
            for rr, cc2 in footprint:
                if 0 <= rr < H and 0 <= cc2 < W:
                    T[(rr, cc2)] = fill
            k += 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
