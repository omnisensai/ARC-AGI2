"""Canonical solver for ARC puzzle d07ae81c.

Structure: the grid is built from two dominant "structural" colors (a stripe
color and a block-fill color) arranged in a tic-tac-toe-like partition. One or
more rare "marker" cells sit inside the partition, each embedded in a region of
one structural color. Every marker shoots diagonal rays (the four diagonals)
across the whole grid. Each cell a ray passes through is repainted: a cell whose
structural color is S becomes the marker color associated with region S (the
marker that lives in an S-colored region).
"""

from collections import Counter


def _region_color(grid, r, c, struct):
    """Vote among the 8 neighbours for which structural color this marker sits in."""
    H, W = len(grid), len(grid[0])
    cnt = Counter()
    for dr in range(-1, 2):
        for dc in range(-1, 2):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < H and 0 <= cc < W and grid[rr][cc] in struct:
                cnt[grid[rr][cc]] += 1
    return cnt.most_common(1)[0][0]


def infer_T(input_grid):
    """Return a latent mask {(r,c): new_color} of cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    counts = Counter(v for row in input_grid for v in row).most_common()
    struct = set(c for c, _ in counts[:2])
    markers = set(c for c, _ in counts[2:])

    marker_cells = [
        (r, c, input_grid[r][c])
        for r in range(H)
        for c in range(W)
        if input_grid[r][c] in markers
    ]

    # Map each structural color -> the marker color whose region uses it.
    struct_to_marker = {}
    for r, c, m in marker_cells:
        s = _region_color(input_grid, r, c, struct)
        struct_to_marker[s] = m

    T = {}
    for r, c, m in marker_cells:
        for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            rr, cc = r + dr, c + dc
            while 0 <= rr < H and 0 <= cc < W:
                s = input_grid[rr][cc]
                if s in struct_to_marker:
                    T[(rr, cc)] = struct_to_marker[s]
                rr += dr
                cc += dc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
