def infer_T(input_grid):
    """Infer the latent transformation mask.

    Each input contains one or more 'plus' shapes: a center cell of color A
    surrounded by 4 orthogonal arms of a single color B (A != B, both non-bg).
    Each plus is expanded into a 5x5 diamond pattern centered on the center:

        A 0 B 0 A
        0 A B A 0
        B B A B B
        0 A B A 0
        A 0 B 0 A

    i.e. along the axes (distance 1 and 2) -> B; on the diagonals (distance 1
    and 2 corners) -> A; center -> A; everything else stays background.
    The pattern is clipped to grid bounds.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    crosses = []
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg:
                continue
            nbrs = []
            ok = True
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < H and 0 <= cc < W):
                    ok = False
                    break
                nbrs.append(input_grid[rr][cc])
            if not ok:
                continue
            if len(set(nbrs)) == 1 and nbrs[0] != bg and nbrs[0] != v:
                crosses.append((r, c, v, nbrs[0]))  # center A, arm B

    T = {}
    for (cr, cc, A, B) in crosses:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                rr, cc2 = cr + dr, cc + dc
                if not (0 <= rr < H and 0 <= cc2 < W):
                    continue
                adr, adc = abs(dr), abs(dc)
                if dr == 0 and dc == 0:
                    col = A
                elif (dr == 0 and adc in (1, 2)) or (dc == 0 and adr in (1, 2)):
                    col = B
                elif adr == adc and adr in (1, 2):
                    col = A
                else:
                    col = None  # leave background
                if col is not None:
                    T[(rr, cc2)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
