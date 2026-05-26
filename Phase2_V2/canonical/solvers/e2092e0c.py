"""Canonical solver for ARC puzzle e2092e0c.

Structure: a marker sits in the top-left 4x4 corner. Its right column (col 3)
and bottom row (row 3) are 5s forming an L-bracket, and the enclosed 3x3 block
(rows 0-2, cols 0-2) is a "key" pattern. Elsewhere in the grid the same 3x3
pattern appears once; the transformation draws a 5x5 hollow square (perimeter of
color 5) around that occurrence, overwriting only the perimeter cells.
"""


def _find_key(grid):
    """Detect the top-left L-bracket marker and return its enclosed 3x3 key."""
    H, W = len(grid), len(grid[0])
    if H < 4 or W < 4:
        return None
    # The bracket: col 3 of rows 0..3 are 5, and row 3 cols 0..3 are 5.
    if not all(grid[r][3] == 5 for r in range(4)):
        return None
    if not all(grid[3][c] == 5 for c in range(4)):
        return None
    return [[grid[r][c] for c in range(3)] for r in range(3)]


def _find_match(grid, key):
    """Find the unique 3x3 occurrence of key outside the top-left marker."""
    H, W = len(grid), len(grid[0])
    found = None
    for r in range(H - 2):
        for c in range(W - 2):
            if r == 0 and c == 0:
                continue  # the marker itself
            if all(grid[r + dr][c + dc] == key[dr][dc]
                   for dr in range(3) for dc in range(3)):
                if found is not None:
                    return None  # ambiguous
                found = (r, c)
    return found


def infer_T(input_grid):
    """Infer a latent mask {(r,c): color} of perimeter cells to overwrite with 5."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    key = _find_key(input_grid)
    if key is None:
        return T
    match = _find_match(input_grid, key)
    if match is None:
        return T
    mr, mc = match
    # 5x5 box surrounds the 3x3 match: box top-left is (mr-1, mc-1).
    r0, c0 = mr - 1, mc - 1
    for dr in range(5):
        for dc in range(5):
            if dr in (0, 4) or dc in (0, 4):  # perimeter only
                r, c = r0 + dr, c0 + dc
                if 0 <= r < H and 0 <= c < W:
                    T[(r, c)] = 5
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
