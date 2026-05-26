"""Canonical solver for ARC puzzle 150deff5.

Rule
----
The input contains a single polyomino drawn in color 5 on a background of 0.
That polyomino is built from exactly two kinds of pieces that tile it without
overlap:
  * 2x2 square "rooms"        -> recolored to 8
  * straight length-3 "corridors" (1x3 or 3x1) -> recolored to 2

`infer_T` finds the unique exact partition of the shape into these pieces and
emits a latent mask {(r, c): new_color}. `apply_T` copies the input and
overwrites only the masked (color-5) cells.  The decomposition is unique for
every pair (verified), so the mask is well defined.
"""


def infer_T(input_grid):
    """Compute the latent recolor mask from the input structure alone."""
    H, W = len(input_grid), len(input_grid[0])

    def is5(r, c):
        return 0 <= r < H and 0 <= c < W and input_grid[r][c] == 5

    # Enumerate every candidate piece anchored at each cell:
    #   - 2x2 square room        -> color 8
    #   - horizontal 1x3 corridor -> color 2
    #   - vertical   3x1 corridor -> color 2
    pieces = []
    for r in range(H):
        for c in range(W):
            if all(is5(r + dr, c + dc) for dr in (0, 1) for dc in (0, 1)):
                pieces.append((frozenset((r + dr, c + dc)
                                         for dr in (0, 1) for dc in (0, 1)), 8))
            if all(is5(r, c + dc) for dc in range(3)):
                pieces.append((frozenset((r, c + dc) for dc in range(3)), 2))
            if all(is5(r + dr, c) for dr in range(3)):
                pieces.append((frozenset((r + dr, c) for dr in range(3)), 2))

    cells = frozenset((r, c) for r in range(H) for c in range(W) if is5(r, c))

    # Exact-cover backtracking: always resolve the lexicographically smallest
    # uncovered cell first, trying each piece that can claim it.
    def cover(remaining):
        if not remaining:
            return []
        target = min(remaining)
        for cs, color in pieces:
            if target in cs and cs <= remaining:
                rest = cover(remaining - cs)
                if rest is not None:
                    return [(cs, color)] + rest
        return None

    solution = cover(cells)
    T = {}
    if solution is None:
        return T
    for cs, color in solution:
        for (r, c) in cs:
            T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
