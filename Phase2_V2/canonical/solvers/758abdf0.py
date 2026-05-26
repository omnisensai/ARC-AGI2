def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Find the baseline: a full row or full column of 0s along one edge.
    def all0_row(r):
        return all(input_grid[r][c] == 0 for c in range(W))

    def all0_col(c):
        return all(input_grid[r][c] == 0 for r in range(H))

    baseline = None  # 'top' / 'bottom' / 'left' / 'right'
    if all0_row(0):
        baseline = 'top'
    elif all0_row(H - 1):
        baseline = 'bottom'
    elif all0_col(0):
        baseline = 'left'
    elif all0_col(W - 1):
        baseline = 'right'

    T = {}  # latent mask: {(r, c): new_color}
    if baseline is None:
        return T

    vertical = baseline in ('top', 'bottom')

    # Measure each perpendicular 8-segment: a run of 8 starting adjacent to the
    # baseline and growing toward the far edge.
    segments = []  # (line_index, run_length)
    if vertical:
        for c in range(W):
            length = 0
            if baseline == 'top':
                r = 1
                while r < H and input_grid[r][c] == 8:
                    length += 1
                    r += 1
            else:  # bottom
                r = H - 2
                while r >= 0 and input_grid[r][c] == 8:
                    length += 1
                    r -= 1
            if length > 0:
                segments.append((c, length))
    else:
        for r in range(H):
            length = 0
            if baseline == 'left':
                c = 1
                while c < W and input_grid[r][c] == 8:
                    length += 1
                    c += 1
            else:  # right
                c = W - 2
                while c >= 0 and input_grid[r][c] == 8:
                    length += 1
                    c -= 1
            if length > 0:
                segments.append((r, length))

    if not segments:
        return T

    maxlen = max(L for _, L in segments)

    # Rule: short segments (length < maxlen) are grown to maxlen with color 8
    # from the baseline; tall segments (length == maxlen) are erased and replaced
    # by a maxlen-long block of color 0 placed at the far edge.
    for idx, L in segments:
        if vertical:
            c = idx
            for r in range(H):
                if input_grid[r][c] == 8:
                    T[(r, c)] = 7
            if L < maxlen:
                if baseline == 'top':
                    for k in range(maxlen):
                        T[(1 + k, c)] = 8
                else:
                    for k in range(maxlen):
                        T[(H - 2 - k, c)] = 8
            else:
                if baseline == 'top':
                    for k in range(maxlen):
                        T[(H - 1 - k, c)] = 0
                else:
                    for k in range(maxlen):
                        T[(k, c)] = 0
        else:
            r = idx
            for c in range(W):
                if input_grid[r][c] == 8:
                    T[(r, c)] = 7
            if L < maxlen:
                if baseline == 'left':
                    for k in range(maxlen):
                        T[(r, 1 + k)] = 8
                else:
                    for k in range(maxlen):
                        T[(r, W - 2 - k)] = 8
            else:
                if baseline == 'left':
                    for k in range(maxlen):
                        T[(r, W - 1 - k)] = 0
                else:
                    for k in range(maxlen):
                        T[(r, k)] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
