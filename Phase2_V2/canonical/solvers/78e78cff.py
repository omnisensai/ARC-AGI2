"""Canonical solver for ARC puzzle 78e78cff.

Rule
----
The grid has three colors: a background (most frequent), a single "marker" cell
(the unique color that appears exactly once), and a "frame" color that forms
corner brackets outlining an octagon/rectangle around the marker.

The marker color floods the interior bounded by the frame brackets (the octagon
body, with the corners cut off by the brackets). Then, wherever the interior
touches the bounding box of the frame through a gap, the marker color projects
straight out to the grid edge as a band/ray.

`infer_T` builds the latent mask of cells that become the marker color;
`apply_T` copies the input and overwrites only those masked cells.
"""

from collections import Counter


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    counts = Counter(v for row in input_grid for v in row)
    bg = counts.most_common(1)[0][0]
    # marker = color that appears exactly once
    marker = next(c for c, n in counts.items() if n == 1)
    # frame = the remaining (non-background, non-marker) color
    frame = next(c for c in counts if c not in (bg, marker))

    fcells = [(r, c) for r in range(H) for c in range(W)
              if input_grid[r][c] == frame]
    fset = set(fcells)
    mpos = next((r, c) for r in range(H) for c in range(W)
                if input_grid[r][c] == marker)

    rs = [r for r, _ in fcells]
    cs = [c for _, c in fcells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)

    # Interior: flood-fill from the marker, confined to the frame bounding box
    # and blocked by frame cells.  The frame corner brackets cut off the
    # rectangle corners, yielding the octagonal body.
    interior = set()
    stack = [mpos]
    while stack:
        r, c = stack.pop()
        if (r, c) in interior:
            continue
        if not (r0 <= r <= r1 and c0 <= c <= c1):
            continue
        if (r, c) in fset:
            continue
        interior.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((r + dr, c + dc))

    # Latent mask: cells to be overwritten with the marker color.
    T = {(r, c): marker for (r, c) in interior}

    # Rays: project straight out wherever the interior touches a bbox edge.
    for (r, c) in interior:
        if r == r0:
            for rr in range(0, r0):
                T[(rr, c)] = marker
        if r == r1:
            for rr in range(r1 + 1, H):
                T[(rr, c)] = marker
        if c == c0:
            for cc in range(0, c0):
                T[(r, cc)] = marker
        if c == c1:
            for cc in range(c1 + 1, W):
                T[(r, cc)] = marker

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
