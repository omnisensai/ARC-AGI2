"""Canonical solver for ARC puzzle 4aab4007.

Structure of every grid:
  - rows 0..1 and columns 0..1 are the background (color 1)
  - row 2 (cols>=2) and column 2 (rows>=2) form an L-shaped border (color 4)
  - region rows>=3, cols>=3 holds an anti-diagonal periodic pattern: every cell
    on a given anti-diagonal d = r+c carries one fixed color, EXCEPT a small
    fixed corner seed (3,3)=3 ; (3,4)=(4,3)=2 ; (3,5)=(5,3)=1.

The transformation repairs "holes" (color 0). infer_T builds a mask that, for
each hole, computes the reconstructed color:
  - holes in the background area  -> 1
  - holes on the border L         -> 4
  - holes in the pattern region   -> consensus color of their anti-diagonal d,
    derived from the surviving (non-hole, non-corner) cells on that diagonal.
apply_T copies the input and overwrites only the masked (hole) cells.
"""


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    # Fixed corner seed cells of the pattern region (never holes); they sit on
    # the small anti-diagonals d=6,7,8 and must not feed the body consensus.
    corner = {(3, 3), (3, 4), (4, 3), (3, 5), (5, 3)}

    # Build per-diagonal consensus from surviving body cells.
    diag_counts = {}
    for r in range(3, H):
        for c in range(3, W):
            if (r, c) in corner:
                continue
            v = input_grid[r][c]
            if v == 0:
                continue
            d = r + c
            bucket = diag_counts.setdefault(d, {})
            bucket[v] = bucket.get(v, 0) + 1
    diag_color = {d: max(b, key=b.get) for d, b in diag_counts.items()}

    # Latent transformation mask: only hole cells receive a new color.
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0:
                continue
            if r < 2 or c < 2:
                # background region
                T[r][c] = 1
            elif r == 2 or c == 2:
                # L-shaped border
                T[r][c] = 4
            else:
                # pattern region: reconstruct from anti-diagonal consensus.
                d = r + c
                if d in diag_color:
                    T[r][c] = diag_color[d]
    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
