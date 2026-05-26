"""Canonical solver for ARC puzzle 0d87d2a6.

Rule:
  Color-1 markers sit on the grid border in matched pairs. A pair on the top
  and bottom edge sharing a column defines a vertical line down that column;
  a pair on the left and right edge sharing a row defines a horizontal line
  across that row. Each such line is the path of a ray.

  The transformation draws every ray (all cells along its column / row) and
  recolors any 2-block (4-connected component of color 2) the ray *touches*
  -- i.e. that overlaps a line cell or is orthogonally adjacent to one --
  entirely to color 1. Background cells lying on a ray path also become
  color 1. Untouched 2-blocks are left unchanged.

infer_T computes the latent mask of cells that must become 1; apply_T copies
the input and overwrites only the masked cells.
"""

from collections import deque


def _components(grid, color):
    """4-connected components of `color` cells, as lists of (r, c)."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and not seen[r][c]:
                q = deque([(r, c)])
                seen[r][c] = True
                cells = []
                while q:
                    rr, cc = q.popleft()
                    cells.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = rr + dr, cc + dc
                        if (0 <= nr < H and 0 <= nc < W
                                and grid[nr][nc] == color and not seen[nr][nc]):
                            seen[nr][nc] = True
                            q.append((nr, nc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Border markers (color 1), grouped into ray lines.
    markers = [(r, c) for r in range(H) for c in range(W)
               if input_grid[r][c] == 1]
    top = {c for r, c in markers if r == 0}
    bottom = {c for r, c in markers if r == H - 1}
    left = {r for r, c in markers if c == 0}
    right = {r for r, c in markers if c == W - 1}
    vert_cols = top & bottom        # vertical rays (top<->bottom)
    horiz_rows = left & right       # horizontal rays (left<->right)

    # All cells lying on a ray path.
    line_cells = set()
    for col in vert_cols:
        for r in range(H):
            line_cells.add((r, col))
    for row in horiz_rows:
        for c in range(W):
            line_cells.add((row, c))

    T = [[None] * W for _ in range(H)]

    # 2-blocks the ray touches (overlap or orthogonal adjacency) become 1.
    for cells in _components(input_grid, 2):
        touched = False
        for (r, c) in cells:
            for dr, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                if (r + dr, c + dc) in line_cells:
                    touched = True
                    break
            if touched:
                break
        if touched:
            for (r, c) in cells:
                T[r][c] = 1

    # Background cells on a ray path become 1.
    for (r, c) in line_cells:
        if input_grid[r][c] == 0:
            T[r][c] = 1

    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
