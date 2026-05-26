"""Canonical solver for ARC puzzle 4e469f39.

Rule: the grid contains one or more box outlines drawn in color 5, each a
rectangle whose border has exactly one missing ("gap") cell. For every box:
  * fill its enclosed interior (all 0-cells inside the bounding box, which
    includes the gap cell) with color 2;
  * emit a "leak" of 2s out of the gap: step one cell outward (perpendicular to
    the gap's edge), then turn 90 degrees away from the adjacent box wall and run
    along that row/column to the grid edge.
"""


def _components_of(grid, color):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    x, y = stack.pop()
                    if (x, y) in seen or not (0 <= x < H and 0 <= y < W):
                        continue
                    if grid[x][y] != color:
                        continue
                    seen.add((x, y))
                    comp.append((x, y))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((x + dr, y + dc))
                comps.append(comp)
    return comps


def infer_T(input_grid):
    """Compute latent mask {(r,c): new_color} from input structure alone."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for comp in _components_of(input_grid, 5):
        rs = [a for a, b in comp]
        cs = [b for a, b in comp]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        if r1 - r0 < 2 or c1 - c0 < 2:
            continue  # too small to enclose an interior

        # interior fill: every 0-cell within the bounding box -> 2 (covers the gap)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if input_grid[r][c] == 0:
                    T[(r, c)] = 2

        # locate the gap: the unique non-5 cell on the box border
        gap = None
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                on_border = (r in (r0, r1)) or (c in (c0, c1))
                if on_border and input_grid[r][c] != 5:
                    gap = (r, c)
        if gap is None:
            continue
        gr, gc = gap

        # outward step (perpendicular to the edge) and the turn direction:
        # turn away from the wall the gap sits next to (toward the interior side).
        if gr == r0:            # top edge
            out_r, out_c = gr - 1, gc
            step = (0, 1) if gc == c0 + 1 else (0, -1)
        elif gr == r1:          # bottom edge
            out_r, out_c = gr + 1, gc
            step = (0, 1) if gc == c0 + 1 else (0, -1)
        elif gc == c0:          # left edge
            out_r, out_c = gr, gc - 1
            step = (1, 0) if gr == r0 + 1 else (-1, 0)
        else:                   # right edge
            out_r, out_c = gr, gc + 1
            step = (1, 0) if gr == r0 + 1 else (-1, 0)

        # leak: first the cell directly outside the gap, then run to grid edge
        rr, cc = out_r, out_c
        sr, sc = step
        if 0 <= rr < H and 0 <= cc < W:
            T[(rr, cc)] = 2
            rr += sr
            cc += sc
            while 0 <= rr < H and 0 <= cc < W:
                T[(rr, cc)] = 2
                rr += sr
                cc += sc
    return T


def apply_T(input_grid, T):
    """Copy input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
