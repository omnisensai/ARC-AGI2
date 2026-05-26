"""Canonical solver for ARC puzzle 95a58926.

Rule: The grid is a lattice of rectangular cells separated by full separator
gridlines (color 5). The interiors of the cells contain scattered "noise" pixels
of a third color. The transformation:
  - clears all cell-interior noise to background (0),
  - keeps the separator gridlines as clean lines of the separator color,
  - paints the noise color at every intersection where a separator row crosses a
    separator column.

Separator rows/columns are detected as lines that contain NO background pixels
(every cell is either the separator color or the noise color).
"""

from collections import Counter


def _palette(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = Counter(v for row in input_grid for v in row)
    bg = 0
    # separator color is the dominant non-background color forming full lines;
    # noise color is the remaining color. Background is the most common (0).
    if bg not in counts:
        bg = max(counts, key=counts.get)
    others = [c for c in counts if c != bg]
    # separator color = the one that appears in full lines (most frequent other)
    others.sort(key=lambda c: -counts[c])
    sep = others[0] if others else bg
    noise = next((c for c in others if c != sep), sep)
    return bg, sep, noise


def infer_T(input_grid):
    """Compute the latent transformation mask: a 2D grid of None/int.

    None means leave as background (0); an int is the color to paint.
    """
    H, W = len(input_grid), len(input_grid[0])
    bg, sep, noise = _palette(input_grid)

    # Separator lines contain no background cells (only sep or noise).
    sep_rows = [r for r in range(H)
                if all(input_grid[r][c] in (sep, noise) for c in range(W))]
    sep_cols = [c for c in range(W)
                if all(input_grid[r][c] in (sep, noise) for r in range(H))]

    T = [[None] * W for _ in range(H)]
    # Paint clean separator rows.
    for r in sep_rows:
        for c in range(W):
            T[r][c] = sep
    # Paint clean separator columns.
    for c in sep_cols:
        for r in range(H):
            T[r][c] = sep
    # Intersections take the noise color.
    for r in sep_rows:
        for c in sep_cols:
            T[r][c] = noise

    # Everywhere else becomes background.
    for r in range(H):
        for c in range(W):
            if T[r][c] is None:
                T[r][c] = bg
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
