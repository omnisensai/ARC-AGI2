from collections import Counter


def infer_T(input_grid):
    """Find the divider cross and mirror all pattern cells into every quadrant.

    The grid is split by one full row and one full column of a single divider
    color into four quadrants. Exactly one quadrant holds a pattern; the
    transformation reflects that pattern across the vertical and horizontal
    divider lines, populating all four quadrants. T maps mirrored target cells
    to their pattern color.
    """
    H, W = len(input_grid), len(input_grid[0])
    rd = next((r for r in range(H) if len(set(input_grid[r])) == 1), None)
    cd = next((c for c in range(W)
               if len(set(input_grid[r][c] for r in range(H))) == 1), None)
    if rd is None or cd is None:
        return {}
    div_color = input_grid[rd][cd]
    counts = Counter(v for row in input_grid for v in row if v != div_color)
    bg = counts.most_common(1)[0][0]

    T = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == div_color or v == bg:
                continue
            for rr in {r, 2 * rd - r}:
                for cc in {c, 2 * cd - c}:
                    if 0 <= rr < H and 0 <= cc < W and rr != rd and cc != cd:
                        T[(rr, cc)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
