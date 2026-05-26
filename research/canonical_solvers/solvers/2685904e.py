def infer_T(input_grid):
    """Latent transformation mask.

    Structure of every input:
      - row 0 holds a run of 8s at the left; its length N is a count marker.
      - one row is a full-width divider of 5s.
      - below the divider sits a "palette" row of mixed colors.
    Rule: in the palette row, find every color that occurs EXACTLY N times.
    For each column holding such a color, raise a vertical bar of that color,
    height N, in the N rows directly above the divider.
    """
    H, W = len(input_grid), len(input_grid[0])

    # N = length of the 8-marker run in the top row.
    N = sum(1 for v in input_grid[0] if v == 8)

    # divider = the all-5s row.
    div = None
    for r in range(H):
        if all(input_grid[r][c] == 5 for c in range(W)):
            div = r
            break

    # palette row = first densely-filled row below the divider.
    palette_row = None
    if div is not None:
        for r in range(div + 1, H):
            if sum(1 for v in input_grid[r] if v != 0) >= W // 2:
                palette_row = r
                break

    T = {}
    if div is None or palette_row is None or N == 0:
        return T

    palette = input_grid[palette_row]
    counts = {}
    for v in palette:
        counts[v] = counts.get(v, 0) + 1
    selected = {v for v, c in counts.items() if c == N}

    for c in range(W):
        v = palette[c]
        if v in selected:
            for h in range(1, N + 1):
                r = div - h
                if 0 <= r < H:
                    T[(r, c)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
