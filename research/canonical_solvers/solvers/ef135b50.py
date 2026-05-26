"""Canonical solver for ARC task ef135b50.

Rule (inferred from input structure alone):
  The grid contains rectangular blocks of color 2 on a background of 0.
  Whenever two blocks face each other horizontally (one entirely to the left
  of the other) and their row ranges overlap, the straight background corridor
  between them -- restricted to the overlapping rows -- is filled with color 9.
  Vertical corridors between blocks are never filled.

This is expressed in canonical latent-T form: infer_T builds a mask of cells to
overwrite (with their new color), apply_T copies the input and writes only those
masked cells.
"""


def _components(grid, H, W):
    """Bounding boxes (r0,r1,c0,c1) of 4-connected components of color 2."""
    seen = [[False] * W for _ in range(H)]
    boxes = []
    for sr in range(H):
        for sc in range(W):
            if grid[sr][sc] == 2 and not seen[sr][sc]:
                stack = [(sr, sc)]
                cells = []
                while stack:
                    r, c = stack.pop()
                    if not (0 <= r < H and 0 <= c < W):
                        continue
                    if seen[r][c] or grid[r][c] != 2:
                        continue
                    seen[r][c] = True
                    cells.append((r, c))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((r + dr, c + dc))
                rs = [r for r, _ in cells]
                cs = [c for _, c in cells]
                boxes.append((min(rs), max(rs), min(cs), max(cs)))
    return boxes


def infer_T(input_grid):
    """Compute the latent transformation mask {(r,c): new_color}."""
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    boxes = _components(input_grid, H, W)
    T = {}
    for i in range(len(boxes)):
        r0a, r1a, c0a, c1a = boxes[i]
        for j in range(len(boxes)):
            if i == j:
                continue
            r0b, r1b, c0b, c1b = boxes[j]
            # box j strictly to the right of box i -> horizontal corridor
            if c1a < c0b:
                ro0 = max(r0a, r0b)
                ro1 = min(r1a, r1b)
                if ro0 <= ro1:
                    corridor = [
                        (r, c)
                        for r in range(ro0, ro1 + 1)
                        for c in range(c1a + 1, c0b)
                    ]
                    if corridor and all(input_grid[r][c] == 0 for r, c in corridor):
                        for r, c in corridor:
                            T[(r, c)] = 9
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
