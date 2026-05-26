"""Canonical solver for ARC task db93a21d.

Rule (inferred from input structure alone):
  The input contains several solid rectangular blocks of color 9 on a 0
  background.  For every block we draw:
    * a frame of color 3 forming a ring of thickness k around the block,
      where k = max(block_height, block_width) // 2 (clipped to the grid),
    * a "shadow" of color 1 the same width as the block, hanging straight
      down from just below the frame's bottom edge to the bottom of the grid.
  Layering precedence (highest wins): original 9 block > frame 3 > shadow 1.
The latent transformation T is the mask of cells to overwrite together with
their target colors; apply_T copies the input and writes only those cells.
"""


def _find_blocks(grid):
    """Connected solid rectangles of color 9 -> (r0, r1, c0, c1) bounding boxes."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    blocks = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 9 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr < 0 or rr >= H or cc < 0 or cc >= W
                            or seen[rr][cc] or grid[rr][cc] != 9):
                        continue
                    seen[rr][cc] = True
                    cells.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((rr + dr, cc + dc))
                rs = [x[0] for x in cells]
                cs = [x[1] for x in cells]
                blocks.append((min(rs), max(rs), min(cs), max(cs)))
    return blocks


def infer_T(input_grid):
    """Return a latent mask {(r, c): new_color} computed from input structure."""
    H, W = len(input_grid), len(input_grid[0])
    blocks = _find_blocks(input_grid)

    T = {}

    # Layer 1: shadows (lowest priority).
    for (r0, r1, c0, c1) in blocks:
        k = max(r1 - r0 + 1, c1 - c0 + 1) // 2
        for r in range(r1 + k + 1, H):
            for c in range(c0, c1 + 1):
                if 0 <= c < W:
                    T[(r, c)] = 1

    # Layer 2: frames (override shadows).
    for (r0, r1, c0, c1) in blocks:
        k = max(r1 - r0 + 1, c1 - c0 + 1) // 2
        for r in range(r0 - k, r1 + k + 1):
            for c in range(c0 - k, c1 + k + 1):
                if 0 <= r < H and 0 <= c < W and not (r0 <= r <= r1 and c0 <= c <= c1):
                    T[(r, c)] = 3

    # Layer 3: the original 9 blocks have highest priority; never mask them.
    for (r0, r1, c0, c1) in blocks:
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                T.pop((r, c), None)

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
