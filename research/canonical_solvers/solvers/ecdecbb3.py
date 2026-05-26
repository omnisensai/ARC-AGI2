"""Canonical solver for ARC task ecdecbb3.

Structure: full rows/columns of 8 act as walls. Each isolated cell of color 2
is a marker that emits rays perpendicular to the wall orientation (both
directions). Each ray travels until it reaches a wall line; where it meets a
wall, a 3x3 box of 8s is stamped (centered on the wall cell, replacing it with
2). The ray cells between the marker and the box become 2.

infer_T builds the latent overwrite mask {(r,c): color} from input structure;
apply_T copies the input and overwrites only masked cells.
"""


def _find_walls(grid):
    """Return ('col', [cols]) or ('row', [rows]) for full lines of 8."""
    H, W = len(grid), len(grid[0])
    full_cols = [c for c in range(W) if all(grid[r][c] == 8 for r in range(H))]
    full_rows = [r for r in range(H) if all(grid[r][c] == 8 for c in range(W))]
    if full_cols:
        return 'col', full_cols
    if full_rows:
        return 'row', full_rows
    return None, []


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    orient, lines = _find_walls(input_grid)
    T = {}
    if orient is None:
        return T

    markers = [(r, c) for r in range(H) for c in range(W)
               if input_grid[r][c] == 2]

    for (mr, mc) in markers:
        if orient == 'col':
            # rays travel horizontally (left & right) along row mr
            line_set = sorted(lines)
            # nearest wall to the left and to the right
            left = max((c for c in line_set if c < mc), default=None)
            right = min((c for c in line_set if c > mc), default=None)
            for wc in (left, right):
                if wc is None:
                    continue
                step = 1 if wc > mc else -1
                # ray of 2s from marker toward wall (exclusive of wall col)
                c = mc
                while c != wc:
                    if 0 <= c < W:
                        T[(mr, c)] = 2
                    c += step
                # 3x3 box centered at (mr, wc)
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = mr + dr, wc + dc
                        if 0 <= rr < H and 0 <= cc < W:
                            T[(rr, cc)] = 2 if (dr == 0 and dc == 0) else 8
        else:
            # horizontal walls: rays travel vertically (up & down) along col mc
            line_set = sorted(lines)
            up = max((r for r in line_set if r < mr), default=None)
            down = min((r for r in line_set if r > mr), default=None)
            for wr in (up, down):
                if wr is None:
                    continue
                step = 1 if wr > mr else -1
                r = mr
                while r != wr:
                    if 0 <= r < H:
                        T[(r, mc)] = 2
                    r += step
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = wr + dr, mc + dc
                        if 0 <= rr < H and 0 <= cc < W:
                            T[(rr, cc)] = 2 if (dr == 0 and dc == 0) else 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
