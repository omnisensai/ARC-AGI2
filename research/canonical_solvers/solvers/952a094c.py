def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Bounding box of all non-background cells = the rectangular box frame.
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    rmin = min(r for r, c in cells); rmax = max(r for r, c in cells)
    cmin = min(c for r, c in cells); cmax = max(c for r, c in cells)

    # Interior corner cells (one step inside the frame corners).
    corners = {
        'tl': (rmin + 1, cmin + 1),
        'tr': (rmin + 1, cmax - 1),
        'bl': (rmax - 1, cmin + 1),
        'br': (rmax - 1, cmax - 1),
    }
    # Each interior corner color is ejected diagonally through the center to the
    # cell one step outside the OPPOSITE frame corner.
    targets = {
        'tl': (rmax + 1, cmax + 1),
        'tr': (rmax + 1, cmin - 1),
        'bl': (rmin - 1, cmax + 1),
        'br': (rmin - 1, cmin - 1),
    }

    T = {}
    for k, (r, c) in corners.items():
        color = input_grid[r][c]
        if color != bg:
            T[(r, c)] = bg  # clear the interior corner
            tr, tc = targets[k]
            if 0 <= tr < H and 0 <= tc < W:
                T[(tr, tc)] = color  # place at opposite outside-diagonal cell
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
