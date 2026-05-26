def infer_T(input_grid):
    """Infer the latent fill mask.

    The grid is divided into rectangular blocks by separator lines (rows/cols
    that contain no background 0). The interior blocks are regions of 0s. Each
    such block is filled with the majority marker color (1 vs 2) found on the
    1/2 markers lying on its four surrounding separator borders. Separator cells
    themselves are never modified.

    T is a 2D mask of None / int; cells set to an int will be overwritten.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Separator rows/cols: contain no 0 cell.
    seprows = [r for r in range(H) if all(input_grid[r][c] != 0 for c in range(W))]
    sepcols = [c for c in range(W) if all(input_grid[r][c] != 0 for r in range(H))]
    sr, sc = set(seprows), set(sepcols)

    # Contiguous row/column segments between separators.
    def segments(n, sep):
        segs, i = [], 0
        while i < n:
            if i in sep:
                i += 1
                continue
            start = i
            while i < n and i not in sep:
                i += 1
            segs.append((start, i - 1))
        return segs

    rsegs = segments(H, sr)
    csegs = segments(W, sc)

    T = [[None] * W for _ in range(H)]

    for (r0, r1) in rsegs:
        for (c0, c1) in csegs:
            # Bordering separator lines (fall back to grid edges).
            up = max([s for s in seprows if s < r0], default=0)
            dn = min([s for s in seprows if s > r1], default=H - 1)
            lf = max([s for s in sepcols if s < c0], default=0)
            rt = min([s for s in sepcols if s > c1], default=W - 1)

            markers = []
            for c in range(c0, c1 + 1):
                if input_grid[up][c] in (1, 2):
                    markers.append(input_grid[up][c])
                if input_grid[dn][c] in (1, 2):
                    markers.append(input_grid[dn][c])
            for r in range(r0, r1 + 1):
                if input_grid[r][lf] in (1, 2):
                    markers.append(input_grid[r][lf])
                if input_grid[r][rt] in (1, 2):
                    markers.append(input_grid[r][rt])

            ones = markers.count(1)
            twos = markers.count(2)
            if ones == 0 and twos == 0:
                continue
            fill = 1 if ones >= twos else 2

            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if input_grid[r][c] == 0:
                        T[r][c] = fill

    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
