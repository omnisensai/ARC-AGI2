"""Canonical latent-T solver for ARC puzzle dc2e9a9d.

Rule: the grid contains several hollow rectangles drawn in color 3, each with a
single one-cell "bump" protruding from one of its four sides. The bump marks a
direction. For each such shape a mirror-image copy is produced and placed on the
side OPPOSITE the bump, with a one-cell gap from the shape's far edge. The copy
is recolored: color 1 when the bump is horizontal (points left/right) and color
8 when the bump is vertical (points up/down). The original shape is left intact;
infer_T returns the set of new (copy) cells and apply_T paints only those.
"""

from collections import deque


def _components(grid):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for i in range(H):
        for j in range(W):
            if grid[i][j] != 0 and not seen[i][j]:
                q = deque([(i, j)])
                seen[i][j] = True
                cells = []
                while q:
                    r, c = q.popleft()
                    cells.append((r, c))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] and grid[nr][nc] != 0:
                                seen[nr][nc] = True
                                q.append((nr, nc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    """Return a dict {(r,c): new_color} of cells to paint (the mirrored copies)."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}

    for cells in _components(input_grid):
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)

        # Cells lying on each border line of the bounding box.
        top = sum(1 for r, c in cells if r == r0)
        bot = sum(1 for r, c in cells if r == r1)
        left = sum(1 for r, c in cells if c == c0)
        right = sum(1 for r, c in cells if c == c1)

        # The bump is the side whose border line holds exactly one cell.
        sides = {"top": top, "bottom": bot, "left": left, "right": right}
        bump_side = min(sides, key=lambda k: sides[k])
        # Require a genuine unique protrusion (==1); otherwise skip this shape.
        if sides[bump_side] != 1:
            continue

        horizontal = bump_side in ("left", "right")
        copy_color = 1 if horizontal else 8

        cset = set(cells)

        if bump_side == "left":
            # copy goes right, mirror across vertical axis just past right edge
            axis2 = 2 * (c1 + 1)
            for (r, c) in cset:
                nr, nc = r, axis2 - c
                if 0 <= nr < H and 0 <= nc < W:
                    T[(nr, nc)] = copy_color
        elif bump_side == "right":
            # copy goes left, mirror across vertical axis just before left edge
            axis2 = 2 * (c0 - 1)
            for (r, c) in cset:
                nr, nc = r, axis2 - c
                if 0 <= nr < H and 0 <= nc < W:
                    T[(nr, nc)] = copy_color
        elif bump_side == "top":
            # copy goes down, mirror across horizontal axis just past bottom edge
            axis2 = 2 * (r1 + 1)
            for (r, c) in cset:
                nr, nc = axis2 - r, c
                if 0 <= nr < H and 0 <= nc < W:
                    T[(nr, nc)] = copy_color
        else:  # bottom
            # copy goes up, mirror across horizontal axis just before top edge
            axis2 = 2 * (r0 - 1)
            for (r, c) in cset:
                nr, nc = axis2 - r, c
                if 0 <= nr < H and 0 <= nc < W:
                    T[(nr, nc)] = copy_color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
