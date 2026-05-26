def infer_T(input_grid):
    """Infer the latent transformation mask {(r,c): new_color}.

    Structure: a background of one dominant color holds 1-markers and
    6-markers. Each 6 is erased (back to background). For every 1, the
    nearest collinear 6 (same row or column) defines a vector 1->6; that
    vector rotated 90 degrees counter-clockwise points from the 1 to where
    a 7-marker is dropped (kept only if it lands inside the grid).
    """
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    ones = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 1]
    sixes = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 6]

    T = {}

    # Erase every 6 marker.
    for (r, c) in sixes:
        T[(r, c)] = bg

    # For each 1, find its nearest collinear 6 and place a rotated 7.
    for (r, c) in ones:
        collinear = [s for s in sixes if s[0] == r or s[1] == c]
        if not collinear:
            continue
        collinear.sort(key=lambda s: abs(s[0] - r) + abs(s[1] - c))
        s = collinear[0]
        vr, vc = s[0] - r, s[1] - c          # vector 1 -> 6
        nr, nc = -vc, vr                     # rotate 90 degrees CCW
        pr, pc = r + nr, c + nc
        if 0 <= pr < H and 0 <= pc < W:
            T[(pr, pc)] = 7

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
