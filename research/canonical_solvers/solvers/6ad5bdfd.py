"""Canonical solver for ARC puzzle 6ad5bdfd.

Rule: One full edge (row or column) is a solid wall of color 2. Every other
connected component (4-connectivity, non-background, non-wall) is a rigid object
that falls toward that wall under "gravity": each object slides one step at a
time toward the wall, stopping when any of its cells would leave the grid or
collide with the wall or another (already-settled) object. Objects keep their
shape and color; objects closer to the wall settle first, the rest stack behind
them. Background is color 0.

The latent transformation T is the mask of cells whose color changes: it records
the final color for every grid cell after gravity (the moved objects and the
emptied background), keyed by (r, c). apply_T overwrites only those cells.
"""

BG = 0
WALL = 2


def _components(grid):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] in (BG, WALL) or seen[r][c]:
                continue
            stack = [(r, c)]
            seen[r][c] = True
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc, grid[cr][cc]))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < H and 0 <= nc < W and not seen[nr][nc]
                            and grid[nr][nc] not in (BG, WALL)):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            objs.append(cells)
    return objs


def _gravity_dir(grid):
    H, W = len(grid), len(grid[0])
    if all(grid[0][c] == WALL for c in range(W)):
        return (-1, 0)
    if all(grid[H - 1][c] == WALL for c in range(W)):
        return (1, 0)
    if all(grid[r][0] == WALL for r in range(H)):
        return (0, -1)
    if all(grid[r][W - 1] == WALL for r in range(H)):
        return (0, 1)
    return (0, 0)


def infer_T(input_grid):
    """Return the latent mask {(r, c): new_color} describing the post-gravity grid."""
    grid = input_grid
    H, W = len(grid), len(grid[0])
    dr, dc = _gravity_dir(grid)
    objs = _components(grid)

    # occupancy: walls + every object cell, so collisions are detected from the start
    occ = set()
    for r in range(H):
        for c in range(W):
            if grid[r][c] == WALL:
                occ.add((r, c))
    for obj in objs:
        for r, c, _ in obj:
            occ.add((r, c))

    moved = True
    while moved:
        moved = False
        for i, obj in enumerate(objs):
            cells = set((r, c) for r, c, _ in obj)
            can = True
            for r, c, _ in obj:
                nr, nc = r + dr, c + dc
                if not (0 <= nr < H and 0 <= nc < W):
                    can = False
                    break
                if (nr, nc) in cells:
                    continue
                if (nr, nc) in occ:
                    can = False
                    break
            if can:
                occ -= cells
                obj2 = [(r + dr, c + dc, col) for r, c, col in obj]
                objs[i] = obj2
                for r, c, _ in obj2:
                    occ.add((r, c))
                moved = True

    # build target grid (walls preserved, objects at final positions, rest bg)
    target = [[BG] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if grid[r][c] == WALL:
                target[r][c] = WALL
    for obj in objs:
        for r, c, col in obj:
            target[r][c] = col

    # mask = cells whose color differs from the input
    T = {}
    for r in range(H):
        for c in range(W):
            if target[r][c] != grid[r][c]:
                T[(r, c)] = target[r][c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
