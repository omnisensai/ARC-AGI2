"""Canonical latent-T solver for ARC puzzle db695cfb.

Rule (inferred from all pairs):
  - Background = most common color. Two special marker colors: 1 and 6.
  - Every pair of `1` markers that is diagonally aligned (|dr| == |dc|, dr != 0)
    is connected by a diagonal line of `1`s between the two endpoints.
  - Wherever a `1` line crosses an input `6`, the `6` keeps its value (6 wins).
  - Any `6` that lies ON one of those `1` connecting diagonals emits a ray along
    the diagonal PERPENDICULAR to that `1` line, spanning the whole grid through
    the `6`'s position. Those ray cells become `6`.
  - `6`s not on any `1` line, and unpaired `1`s, stay as single cells.

infer_T returns a latent mask {(r,c): new_color}; apply_T overwrites only those.
"""


def _diag_cells(a, b):
    """Inclusive diagonal cell list from a to b (a,b diagonally aligned)."""
    r0, c0 = a
    r1, c1 = b
    sr = 1 if r1 > r0 else -1
    sc = 1 if c1 > c0 else -1
    n = abs(r1 - r0)
    return [(r0 + sr * k, c0 + sc * k) for k in range(n + 1)]


def _ray_cells(pos, dr, dc, H, W):
    """Full diagonal line through pos in direction (dr,dc), both ways, in-grid."""
    r0, c0 = pos
    cells = []
    # walk backwards
    r, c = r0, c0
    while 0 <= r < H and 0 <= c < W:
        r -= dr
        c -= dc
    r += dr
    c += dc
    while 0 <= r < H and 0 <= c < W:
        cells.append((r, c))
        r += dr
        c += dc
    return cells


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    ones = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 1]
    sixes = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 6]
    six_set = set(sixes)

    T = {}

    # 1) Connect every diagonally-aligned pair of `1`s with a `1` diagonal.
    one_lines = []  # (direction-tuple, set-of-cells) for each connecting diagonal
    for i in range(len(ones)):
        for j in range(i + 1, len(ones)):
            a, b = ones[i], ones[j]
            dr = b[0] - a[0]
            dc = b[1] - a[1]
            if dr != 0 and abs(dr) == abs(dc):
                cells = _diag_cells(a, b)
                line_dir = (1 if dr > 0 else -1, 1 if dc > 0 else -1)
                one_lines.append((line_dir, set(cells)))
                for (r, c) in cells:
                    # `6` wins on overlap; otherwise the line is `1`.
                    if (r, c) in six_set:
                        continue
                    T[(r, c)] = 1

    # 2) Any `6` sitting on a `1` connecting line emits a perpendicular ray.
    for (r, c) in sixes:
        for line_dir, cellset in one_lines:
            if (r, c) in cellset:
                # perpendicular diagonal direction
                pr = (line_dir[0], -line_dir[1])
                for (rr, cc) in _ray_cells((r, c), pr[0], pr[1], H, W):
                    T[(rr, cc)] = 6
                break  # one ray per six is enough (lines share direction class)

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
