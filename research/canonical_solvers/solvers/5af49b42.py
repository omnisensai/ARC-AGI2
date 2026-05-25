def infer_T(input_grid):
    """Compute the latent stamp mask {(r,c): color}.

    Edge rows (top row 0 and bottom row H-1) act as a legend: each contiguous
    run of non-zero cells there is a color "sequence". Every other non-zero
    pixel is a marker; its color identifies which sequence to stamp and at which
    offset, so the sequence is laid horizontally so the matching element sits on
    the marker's column.
    """
    H, W = len(input_grid), len(input_grid[0])

    sequences = []
    legend_rows = set()
    for r in (0, H - 1):
        c = 0
        found = False
        while c < W:
            if input_grid[r][c] != 0:
                seq = []
                while c < W and input_grid[r][c] != 0:
                    seq.append(input_grid[r][c])
                    c += 1
                if len(seq) >= 2:
                    sequences.append(seq)
                    found = True
            else:
                c += 1
        if found:
            legend_rows.add(r)

    T = {}
    for r in range(H):
        if r in legend_rows:
            continue
        for c in range(W):
            v = input_grid[r][c]
            if v == 0:
                continue
            for seq in sequences:
                if v in seq:
                    start = c - seq.index(v)
                    for k, val in enumerate(seq):
                        cc = start + k
                        if 0 <= cc < W:
                            T[(r, cc)] = val
                    break
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), val in T.items():
        out[r][c] = val
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
