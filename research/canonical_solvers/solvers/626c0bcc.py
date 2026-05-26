"""Canonical solver for ARC puzzle 626c0bcc.

Rule: The 8-colored cells form a region that tiles exactly into pieces whose
bounding box is 2x2. Four piece types occur, each mapped to a fixed color by
its shape within the 2x2 box:

    color 1: full 2x2 square      [(0,0),(0,1),(1,0),(1,1)]
    color 2: L missing top-left   [(0,1),(1,0),(1,1)]
    color 3: L missing bottom-left[(0,0),(0,1),(1,1)]
    color 4: L missing top-right  [(0,0),(1,0),(1,1)]

The region admits a unique exact-cover partition by these pieces. infer_T finds
that partition (backtracking exact cover) and records each cell's piece color as
the latent mask; apply_T overwrites the masked cells.
"""

# piece-shape (cell offsets within 2x2 box) -> output color
SHAPES = {
    1: [(0, 0), (0, 1), (1, 0), (1, 1)],
    2: [(0, 1), (1, 0), (1, 1)],
    3: [(0, 0), (0, 1), (1, 1)],
    4: [(0, 0), (1, 0), (1, 1)],
}


def infer_T(input_grid):
    """Return {(r, c): new_color} mask by exact-cover tiling of the 8-cells."""
    H, W = len(input_grid), len(input_grid[0])
    eight = set(
        (r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8
    )
    order = sorted(eight)
    assign = {}

    def place_options(cell):
        # all pieces that, when their lex-min offset aligns to `cell`, lie
        # entirely on 8-cells (cell is the lex-first cell of the piece)
        r, c = cell
        opts = []
        for col, off in SHAPES.items():
            mino = min(off)
            br, bc = r - mino[0], c - mino[1]
            box = set((br + dr, bc + dc) for dr, dc in off)
            if box <= eight:
                opts.append((col, box))
        return opts

    def bt(covered):
        if len(covered) == len(eight):
            return True
        cell = next(c for c in order if c not in covered)
        for col, box in place_options(cell):
            if box & covered:
                continue
            for b in box:
                assign[b] = col
            if bt(covered | box):
                return True
            for b in box:
                del assign[b]
        return False

    bt(set())
    return dict(assign)


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
