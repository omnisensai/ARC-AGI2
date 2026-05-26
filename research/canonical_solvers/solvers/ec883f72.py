"""Canonical latent-T solver for ARC puzzle ec883f72.

Rule: the grid contains a hollow "box" drawn in a border color whose bounding box
strictly encloses an inner shape of a second color. The box is closed on some
edges (full border lines) and open on others. At every corner of the box where
two closed edges meet, a diagonal ray of the inner color is fired outward
(away from the box), continuing to the grid edge. The latent mask T marks those
ray cells; apply_T paints them the inner color.
"""

from collections import Counter


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), max(rs), min(cs), max(cs)


def infer_T(input_grid):
    """Compute the latent transformation mask {(r, c): color} from input structure."""
    H, W = len(input_grid), len(input_grid[0])
    counts = Counter(v for row in input_grid for v in row)
    bg = counts.most_common(1)[0][0]
    nonbg = [c for c in counts if c != bg]
    T = {}
    if len(nonbg) != 2:
        return T

    cells = {
        col: [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == col]
        for col in nonbg
    }
    a, b = nonbg
    abb, bbb = _bbox(cells[a]), _bbox(cells[b])

    def contains(outer, inner):
        return (outer[0] <= inner[0] and inner[1] <= outer[1]
                and outer[2] <= inner[2] and inner[3] <= outer[3])

    if contains(abb, bbb):
        border, inner = a, b
    elif contains(bbb, abb):
        border, inner = b, a
    else:
        return T

    r0, r1, c0, c1 = _bbox(cells[border])
    bset = set(cells[border])
    top = all((r0, c) in bset for c in range(c0, c1 + 1))
    bot = all((r1, c) in bset for c in range(c0, c1 + 1))
    left = all((r, c0) in bset for r in range(r0, r1 + 1))
    right = all((r, c1) in bset for r in range(r0, r1 + 1))

    # Each corner: (row, col, edge_a_closed, edge_b_closed, outward diagonal step).
    corners = [
        (r0, c0, top, left, (-1, -1)),
        (r0, c1, top, right, (-1, 1)),
        (r1, c0, bot, left, (1, -1)),
        (r1, c1, bot, right, (1, 1)),
    ]
    for cr, cc, e1, e2, (dr, dc) in corners:
        if e1 and e2:
            r, c = cr + dr, cc + dc
            while 0 <= r < H and 0 <= c < W:
                T[(r, c)] = inner
                r += dr
                c += dc
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
