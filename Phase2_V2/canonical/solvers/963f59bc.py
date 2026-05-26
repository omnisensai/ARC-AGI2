def infer_T(input_grid):
    """Latent mask: stamp a mirrored copy of the 1-shape at each colored marker.

    Structure of the puzzle: one multi-cell template shape (the most common
    non-zero color) plus one-or-more single-cell markers of other colors.
    Each marker projects a mirror image of the template:
      - marker sharing a ROW with the template -> horizontal mirror (flipH)
      - marker sharing a COLUMN with the template -> vertical mirror (flipV)
    The mirrored copy is positioned so the template's anchor cell (the cell
    in the marker's row/column nearest the marker) lands on the marker.
    """
    H, W = len(input_grid), len(input_grid[0])
    cellsby = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0:
                cellsby.setdefault(v, []).append((r, c))
    if not cellsby:
        return {}
    # template = color with the most cells
    shape_color = max(cellsby, key=lambda k: len(cellsby[k]))
    shape = cellsby[shape_color]
    T = {}
    for col, cl in cellsby.items():
        if col == shape_color:
            continue
        for (mr, mc) in cl:
            same_row = [(r, c) for (r, c) in shape if r == mr]
            same_col = [(r, c) for (r, c) in shape if c == mc]
            if same_row and not same_col:
                mode = 'H'
                anchor = min(same_row, key=lambda rc: abs(rc[1] - mc))
            elif same_col and not same_row:
                mode = 'V'
                anchor = min(same_col, key=lambda rc: abs(rc[0] - mr))
            elif same_row:
                mode = 'H'
                anchor = min(same_row, key=lambda rc: abs(rc[1] - mc))
            else:
                continue
            if mode == 'H':
                f = lambda r, c: (r, -c)
            else:
                f = lambda r, c: (-r, c)
            ar, ac = f(*anchor)
            dr, dc = mr - ar, mc - ac
            for (r, c) in shape:
                tr, tc = f(r, c)
                rr, cc = tr + dr, tc + dc
                if 0 <= rr < H and 0 <= cc < W:
                    T[(rr, cc)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
