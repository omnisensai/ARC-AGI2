"""Canonical solver for ARC puzzle 05f2a901.

Rule: the grid contains one blue (2) shape and one azure (8) block. The blue
shape slides along the single axis that separates it from the 8-block, in the
direction of the 8-block, until its bounding box is immediately adjacent to the
8-block's bounding box (one cell of gap closed). The 8-block stays fixed. The
latent transformation T clears the original 2 cells (set to background 0) and
paints the 2 cells at their translated positions.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    c2 = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 2]
    c8 = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]
    if not c2 or not c8:
        return {}

    r2min = min(r for r, c in c2); r2max = max(r for r, c in c2)
    c2min = min(c for r, c in c2); c2max = max(c for r, c in c2)
    r8min = min(r for r, c in c8); r8max = max(r for r, c in c8)
    c8min = min(c for r, c in c8); c8max = max(c for r, c in c8)

    # bounding-box centers, used to pick the separation axis and direction
    cr2 = (r2min + r2max) / 2.0; cc2 = (c2min + c2max) / 2.0
    cr8 = (r8min + r8max) / 2.0; cc8 = (c8min + c8max) / 2.0

    if abs(cr8 - cr2) >= abs(cc8 - cc2):
        # move vertically toward the 8-block
        if cr8 > cr2:
            dr = (r8min - 1) - r2max  # 8 below: bring 2's bottom just above it
        else:
            dr = (r8max + 1) - r2min  # 8 above: bring 2's top just below it
        dc = 0
    else:
        # move horizontally toward the 8-block
        dr = 0
        if cc8 > cc2:
            dc = (c8min - 1) - c2max  # 8 to the right
        else:
            dc = (c8max + 1) - c2min  # 8 to the left

    T = {}
    for (r, c) in c2:
        T[(r, c)] = 0          # clear original blue cells
    for (r, c) in c2:
        T[(r + dr, c + dc)] = 2  # paint blue at translated positions (wins overlaps)
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H, W = len(out), len(out[0])
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
