import math


def infer_T(input_grid):
    """Build a latent transformation mask {(r,c): color}.

    Rule: each column that contains colored marks describes a pyramid. The total
    number of colored cells in that column is a perfect square K*K; the pyramid
    has K rows (widths 1,3,5,...,2K-1) anchored at the bottom of the grid and
    centered horizontally on that column. The colors, read top-to-bottom in the
    input column, form a stream that fills the pyramid cell-by-cell, row by row
    from the apex down. The original column marks are cleared.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    T = {}

    for c in range(W):
        # Collect colored cells in this column, top to bottom.
        cells = [(r, input_grid[r][c]) for r in range(H) if input_grid[r][c] != 0]
        if not cells:
            continue

        # Clear the original marks for this column.
        for r, _ in cells:
            T[(r, c)] = 0

        # Build the color stream (preserving runs but just as a flat list).
        stream = [v for _, v in cells]
        total = len(stream)

        # Pyramid height: total must be a perfect square (1+3+...+(2K-1)=K^2).
        K = math.isqrt(total)
        if K * K != total:
            continue

        # Fill the pyramid: row k (apex k=0) has width 2k+1, bottom row at H-1.
        idx = 0
        for k in range(K):
            width = 2 * k + 1
            rr = H - K + k
            half = width // 2
            for j in range(width):
                cc = c - half + j
                if 0 <= rr < H and 0 <= cc < W:
                    T[(rr, cc)] = stream[idx]
                idx += 1

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H = len(out)
    W = len(out[0]) if H else 0
    for (r, c), color in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
