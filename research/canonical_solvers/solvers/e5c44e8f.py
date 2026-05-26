"""Canonical latent-T solver for ARC puzzle e5c44e8f.

Rule (inferred from all train pairs):
  - The grid has a single seed cell of color 3 and scattered cells of color 2.
  - From the seed, draw an outward square spiral in color 3.
    Direction order: Up, Right, Down, Left (repeating).
    Segment lengths: 2, 2, 4, 4, 6, 6, 8, 8, ... (each pair grows by 2).
  - Cells of the spiral path that fall outside the grid are simply skipped
    (the spiral keeps going and may re-enter the grid).
  - The spiral STOPS the moment its path reaches an in-bounds cell that
    currently holds a 2; that 2 cell is left untouched and nothing further
    is drawn.

infer_T computes the latent mask of cells to set to 3.
apply_T copies the input and overwrites only the masked cells.
"""


def _find_seed(grid):
    H, W = len(grid), len(grid[0])
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 3:
                return (r, c)
    return None


def infer_T(input_grid):
    """Return latent transformation mask as {(r,c): 3} for cells to paint."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    seed = _find_seed(input_grid)
    if seed is None:
        return T

    # Spiral parameters.
    dirs = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # Up, Right, Down, Left

    # Segment length sequence: 2,2,4,4,6,6,8,8,...
    def seg_lengths():
        k = 2
        while True:
            yield k
            yield k
            k += 2

    r, c = seed
    # Seed itself is part of the spiral.
    T[(r, c)] = 3

    di = 0
    stopped = False
    gen = seg_lengths()
    # Bound the number of segments generously relative to grid size.
    max_segments = 4 * (H + W) + 8
    seg_count = 0
    while not stopped and seg_count < max_segments:
        L = next(gen)
        dr, dc = dirs[di % 4]
        for _ in range(L):
            r += dr
            c += dc
            if 0 <= r < H and 0 <= c < W:
                if input_grid[r][c] == 2:
                    # Spiral halts at the first 2 it reaches; leave it.
                    stopped = True
                    break
                T[(r, c)] = 3
            # Out-of-bounds cells are skipped; the spiral continues.
        di += 1
        seg_count += 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
