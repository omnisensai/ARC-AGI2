def infer_T(input_grid):
    """Build a latent transformation mask {(r,c): color}.

    For every marker cell (color 3) found in the input, draw a fixed
    'frame' template centered on that marker:
      - row r-2, cols c-2..c+2 : color 5 (top bar)
      - cell (r-1, c)          : color 5 (inner stem)
      - col c-2, rows r-1..r+1 : color 2 (left wall)
      - col c+2, rows r-1..r+1 : color 2 (right wall)
      - row r+2, cols c-2..c+2 : color 8 (bottom bar)
      - row r+2, every other col: color 2 (the bottom bar's wings span the row)
    The marker (3) itself is left untouched.
    """
    H, W = len(input_grid), len(input_grid[0])
    markers = [(r, c) for r in range(H) for c in range(W)
               if input_grid[r][c] == 3]

    T = {}

    def put(r, c, color):
        if 0 <= r < H and 0 <= c < W and input_grid[r][c] != 3:
            T[(r, c)] = color

    for (r, c) in markers:
        # bottom row: full-width wings of 2, then the 8 bar on top
        rb = r + 2
        if 0 <= rb < H:
            for cc in range(W):
                put(rb, cc, 2)
            for cc in range(c - 2, c + 3):
                put(rb, cc, 8)
        # top bar of 5
        for cc in range(c - 2, c + 3):
            put(r - 2, cc, 5)
        # inner vertical stem of 5
        put(r - 1, c, 5)
        # left and right walls of 2
        for rr in range(r - 1, r + 2):
            put(rr, c - 2, 2)
            put(rr, c + 2, 2)

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
