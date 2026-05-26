"""Canonical latent-T solver for ARC puzzle 55783887.

Rule (derived from ALL pairs):
  - Background = most common color. Foreground markers are single colored cells
    (colors 1 and 6).
  - Two same-colored markers that lie on a common diagonal define the primary
    AXIS line; if several such pairs exist, the one spanning the longest diagonal
    wins. The cells between the two endpoints (inclusive) are drawn in the axis
    color (existing marker cells keep their color).
  - Any *other*-colored marker that lies exactly on the axis acts as a source and
    emits a straight diagonal ray PERPENDICULAR to the axis, in both directions,
    travelling until it leaves the grid. Those cells are painted with the source
    marker's color (marker cells are never overwritten).

infer_T builds an explicit {(r,c): color} mask of all cells to paint; apply_T
copies the input and overwrites only the masked cells.
"""

from collections import Counter


def _background(grid):
    counts = Counter(v for row in grid for v in row)
    return counts.most_common(1)[0][0]


def _ray(r, c, dr, dc, H, W):
    """Straight diagonal ray from (r,c), exclusive of start, until it exits."""
    cells = []
    while True:
        r += dr
        c += dc
        if not (0 <= r < H and 0 <= c < W):
            break
        cells.append((r, c))
    return cells


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    markers = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    mcol = {(r, c): input_grid[r][c] for (r, c) in markers}
    mset = set(markers)

    # Candidate axes: pairs of same-colored markers sharing a diagonal.
    cands = []
    for i in range(len(markers)):
        for j in range(i + 1, len(markers)):
            A, B = markers[i], markers[j]
            if mcol[A] != mcol[B] or A == B:
                continue
            if abs(A[0] - B[0]) != abs(A[1] - B[1]):
                continue  # not on a 45-degree diagonal
            length = abs(A[0] - B[0])
            cands.append((length, A, B, mcol[A]))

    T = {}
    if not cands:
        return T

    # Primary axis = longest diagonal pair.
    cands.sort(key=lambda t: t[0], reverse=True)
    _, A, B, axis_col = cands[0]
    sr = 1 if B[0] > A[0] else -1
    sc = 1 if B[1] > A[1] else -1

    # Draw the axis line between A and B (inclusive); keep marker cells intact.
    axis_cells = []
    r, c = A
    while True:
        axis_cells.append((r, c))
        if (r, c) == B:
            break
        r += sr
        c += sc
    axis_set = set(axis_cells)
    for (r, c) in axis_cells:
        if (r, c) not in mset:
            T[(r, c)] = axis_col

    # Perpendicular rays from other-colored markers lying on the axis.
    perp = [(sr, -sc), (-sr, sc)]
    for m in markers:
        if m not in axis_set or mcol[m] == axis_col:
            continue
        for dr, dc in perp:
            for (rr, cc) in _ray(m[0], m[1], dr, dc, H, W):
                if (rr, cc) not in mset:
                    T[(rr, cc)] = mcol[m]

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
