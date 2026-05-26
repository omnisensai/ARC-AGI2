def infer_T(input_grid):
    """Infer latent transformation mask.

    Each cell of color 4 is enclosed by a solid square ring of color 2.
    The square is centered on the 4 with half-width R = d - 1, where d is the
    minimum Chebyshev distance from that 4 to any cell of color 5. The 4 itself
    keeps its value; any 5 lying inside the box keeps its value (not overwritten).
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    fours = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 4]
    fives = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 5]

    T = {}
    for (fr, fc) in fours:
        if not fives:
            continue
        d = min(max(abs(fr - vr), abs(fc - vc)) for (vr, vc) in fives)
        R = d - 1
        if R < 1:
            continue
        for r in range(fr - R, fr + R + 1):
            for c in range(fc - R, fc + R + 1):
                if not (0 <= r < H and 0 <= c < W):
                    continue
                if input_grid[r][c] == 0:
                    T[(r, c)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
