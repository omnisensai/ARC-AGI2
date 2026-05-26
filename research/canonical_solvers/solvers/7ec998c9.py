from collections import Counter


def infer_T(input_grid):
    """Infer the latent change mask {(r,c): color} from input structure.

    There is a single non-background marker cell. The transform draws the
    marker's full column as color 1 (minus the marker itself), then attaches
    a horizontal arm at the top row and another at the bottom row, each
    running from the marker column to a corner. The two arms occupy opposite
    diagonal corners (a Z/S shape). If the marker is horizontally centered
    the top arm goes right and the bottom arm goes left (TR/BL); otherwise
    the top arm goes left and the bottom arm goes right (TL/BR).
    """
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter(v for row in input_grid for v in row)
    bg = cnt.most_common(1)[0][0]

    mr = mc = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg:
                mr, mc = r, c
    if mr is None:
        return {}

    T = {}
    # Full vertical line through the marker's column (skip the marker cell).
    for r in range(H):
        if r != mr:
            T[(r, mc)] = 1

    centered = (W % 2 == 1 and mc == (W - 1) // 2)
    if centered:
        # top arm -> right corner, bottom arm -> left corner
        for c in range(mc, W):
            T[(0, c)] = 1
        for c in range(0, mc + 1):
            T[(H - 1, c)] = 1
    else:
        # top arm -> left corner, bottom arm -> right corner
        for c in range(0, mc + 1):
            T[(0, c)] = 1
        for c in range(mc, W):
            T[(H - 1, c)] = 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
