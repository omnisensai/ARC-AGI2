from collections import Counter


def _region_color(r, c, diag, bg, frame):
    """True color of cell (r,c) given the panel's layered structure."""
    if r < 2 or c < 2:
        return bg            # outer background margin
    if r == 2 or c == 2:
        return frame         # the L-shaped frame (top row / left column)
    if (r, c) in {(3, 3), (3, 4), (4, 3), (4, 4)}:
        return None          # fixed 2x2 seed marker, never recolored
    cnt = diag.get(r + c)
    return cnt.most_common(1)[0][0] if cnt else None


def infer_T(input_grid):
    """Latent repair mask: restore cells damaged by 0-holes.

    The panel has a layered structure: an outer background (1) margin in rows
    0-1 and cols 0-1, an L-shaped frame (4) along row 2 and col 2, and a striped
    interior (rows>=3, cols>=3) whose color is constant along each anti-diagonal
    r+c. A small 2x2 seed marker at the interior corner is fixed. Holes (0) are
    damage; each region's true color is recovered from the surviving evidence
    (background = dominant color, frame = its constant value, diagonals = per-
    diagonal consensus), and only the holes are masked for repair.
    """
    H, W = len(input_grid), len(input_grid[0])
    R0, C0 = 3, 3  # top-left of the striped interior

    # Dominant non-hole color = background.
    counts = Counter()
    for row in input_grid:
        for v in row:
            if v != 0:
                counts[v] += 1
    bg = counts.most_common(1)[0][0]

    # Frame color: the constant value along row 2 / col 2 (surviving cells).
    frame_counts = Counter()
    for c in range(2, W):
        v = input_grid[2][c]
        if v != 0:
            frame_counts[v] += 1
    for r in range(2, H):
        v = input_grid[r][2]
        if v != 0:
            frame_counts[v] += 1
    frame = frame_counts.most_common(1)[0][0] if frame_counts else bg

    # Per-anti-diagonal consensus color over surviving interior (non-seed) cells.
    seed = {(3, 3), (3, 4), (4, 3), (4, 4)}
    diag = {}
    for r in range(R0, H):
        for c in range(C0, W):
            if (r, c) in seed:
                continue
            v = input_grid[r][c]
            if v == 0:
                continue
            diag.setdefault(r + c, Counter())[v] += 1

    # Mask only the holes, to their recovered true color.
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0:
                T[r][c] = _region_color(r, c, diag, bg, frame)
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
