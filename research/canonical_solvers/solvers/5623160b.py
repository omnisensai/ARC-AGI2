"""Canonical solver for ARC puzzle 5623160b.

Rule: the background is the most frequent color (7 in all examples) and the
color 9 forms fixed "anchor" structures. Every other colored object is attached
to an anchor: exactly one of its cells is cardinally adjacent to a 9-cell. The
object is launched away from that anchor along the cardinal direction implied by
the offset (anchor -> object), preserving its shape, sliding until its leading
edge reaches the grid border. Anchors (9) and background stay put.
"""

ANCHOR = 9


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Same-color 4-connected components of non-background, non-anchor cells.
    seen = [[False] * W for _ in range(H)]
    objects = []
    for r in range(H):
        for c in range(W):
            if seen[r][c] or input_grid[r][c] in (bg, ANCHOR):
                continue
            col = input_grid[r][c]
            stack = [(r, c)]
            cells = []
            while stack:
                rr, cc = stack.pop()
                if not (0 <= rr < H and 0 <= cc < W):
                    continue
                if seen[rr][cc] or input_grid[rr][cc] != col:
                    continue
                seen[rr][cc] = True
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((rr + dr, cc + dc))
            objects.append(cells)

    anchors = set(
        (r, c)
        for r in range(H)
        for c in range(W)
        if input_grid[r][c] == ANCHOR
    )

    # Latent mask: dict (r, c) -> new color. Each object erases its source cells
    # (paint background) then paints the translated cells.
    T = {}
    for cells in objects:
        direction = None
        for (r, c) in cells:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (r + dr, c + dc) in anchors:
                    direction = (-dr, -dc)  # offset of object from its anchor
                    break
            if direction is not None:
                break
        if direction is None:
            continue

        dr, dc = direction
        # Maximum shift k >= 0 keeping every cell inside the grid (slide to wall).
        kmax = None
        for (r, c) in cells:
            if dr == 1:
                lim = (H - 1) - r
            elif dr == -1:
                lim = r
            elif dc == 1:
                lim = (W - 1) - c
            else:
                lim = c
            kmax = lim if kmax is None else min(kmax, lim)
        k = kmax

        colmap = {(r, c): input_grid[r][c] for (r, c) in cells}
        for (r, c) in cells:
            T[(r, c)] = bg
        for (r, c) in cells:
            T[(r + dr * k, c + dc * k)] = colmap[(r, c)]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
