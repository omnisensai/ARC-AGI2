def infer_T(input_grid):
    """Find the unique solid filled monochrome rectangle (single nonzero color,
    every cell inside it that color, at least 2x2). Return (mask, color) where
    mask is the set of cells covered by that rectangle."""
    H, W = len(input_grid), len(input_grid[0])

    best = None  # (area, color, r0, r1, c0, c1)
    # Enumerate maximal solid monochrome rectangles anchored at each top-left
    # corner: for each starting cell, grow downward keeping the minimum
    # contiguous same-color row width seen so far.
    for r0 in range(H):
        for c0 in range(W):
            color = input_grid[r0][c0]
            if color == 0:
                continue
            cur_w = None
            h = 0
            r = r0
            while r < H:
                w_row = 0
                while c0 + w_row < W and input_grid[r][c0 + w_row] == color:
                    w_row += 1
                if w_row == 0:
                    break
                cur_w = w_row if cur_w is None else min(cur_w, w_row)
                if cur_w == 0:
                    break
                h += 1
                area = h * cur_w
                if h >= 2 and cur_w >= 2:
                    if best is None or area > best[0]:
                        best = (area, color, r0, r0 + h - 1, c0, c0 + cur_w - 1)
                r += 1

    if best is None:
        return set(), 0
    _, color, r0, r1, c0, c1 = best
    mask = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
    return mask, color


def apply_T(input_grid, T):
    """Blank canvas, then write only the masked rectangle cells."""
    mask, color = T
    H, W = len(input_grid), len(input_grid[0])
    out = [[0] * W for _ in range(H)]
    for (r, c) in mask:
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
