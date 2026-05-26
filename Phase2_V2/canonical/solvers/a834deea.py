"""Canonical solver for ARC puzzle a834deea.

Rule: the grid contains several rectangular boxes drawn with color 0 (a 0
border around a 3x3 interior of 0/8 cells). Inside each box, every interior
cell that is 0 is recolored according to a fixed 3x3 positional template;
interior cells that are 8 (holes) are left untouched.

Template (interior row, col -> color):
    [[1, 7, 6],
     [4, 0, 5],
     [2, 9, 3]]

infer_T scans the input for the 0-connected box components, locates each
3x3 interior, and builds a latent mask {(r, c): new_color} of the cells to
overwrite. apply_T copies the input and paints only the masked cells.
"""

TEMPLATE = [[1, 7, 6],
            [4, 0, 5],
            [2, 9, 3]]


def _components(grid):
    """8-connected components of color-0 cells (each box outline + interior)."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 0 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if not (0 <= a < H and 0 <= b < W):
                        continue
                    if seen[a][b] or grid[a][b] != 0:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((a + dr, b + dc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    """Build the latent overwrite mask from the input structure alone."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for cells in _components(input_grid):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        # Expect a box: rectangular border with a 3x3 interior.
        if (r1 - r0) != 4 or (c1 - c0) != 4:
            continue
        for i in range(3):
            for j in range(3):
                rr, cc = r0 + 1 + i, c0 + 1 + j
                if input_grid[rr][cc] == 0:
                    T[(rr, cc)] = TEMPLATE[i][j]
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
