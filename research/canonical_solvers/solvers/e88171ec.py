"""Canonical solver for ARC puzzle e88171ec.

Rule: the grid is a noisy field of two colors (a background color 0 and a
foreground color). Somewhere in it there is one maximal solid rectangle made
entirely of the background color. The interior of that rectangle (every cell
except its one-cell-thick border ring) is recolored to 8.

infer_T finds the largest all-background rectangle and marks its interior;
apply_T overwrites only those masked cells with 8.
"""


def _most_common_color(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _largest_uniform_rect(grid, bg):
    """Return (r0, r1, c0, c1) of the maximal-area rectangle whose cells are
    all equal to bg, using the classic largest-rectangle-in-histogram method."""
    H, W = len(grid), len(grid[0])
    heights = [0] * W
    best = None
    best_area = 0
    for r in range(H):
        for c in range(W):
            heights[c] = heights[c] + 1 if grid[r][c] == bg else 0
        stack = []  # entries: (start_col, height)
        for c in range(W + 1):
            h = heights[c] if c < W else 0
            start = c
            while stack and stack[-1][1] > h:
                s, sh = stack.pop()
                area = sh * (c - s)
                if area > best_area:
                    best_area = area
                    best = (r - sh + 1, r, s, c - 1)
                start = s
            stack.append((start, h))
    return best


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _most_common_color(input_grid)
    T = [[None] * W for _ in range(H)]
    rect = _largest_uniform_rect(input_grid, bg)
    if rect is None:
        return T
    r0, r1, c0, c1 = rect
    # Fill the interior (exclude the one-cell border ring) with 8.
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            T[r][c] = 8
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
