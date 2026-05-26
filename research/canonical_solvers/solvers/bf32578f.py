"""Canonical latent-T solver for ARC puzzle bf32578f.

Rule (inferred from all train+test pairs):
The input contains a single open arc / bracket drawn in one foreground color on a
background of the most common color. The arc is the LEFT wall (curved or straight)
of a closed shape that opens toward the right. Its rightmost column ``cmax`` marks
the opening (the vertical axis of symmetry sits at ``cmax + 0.5``).

To produce the output we close and fill the shape:
  * For every row that contains arc cells, take that row's INNER edge ``inner`` =
    the rightmost arc column in the row (the edge nearest the opening).
  * The filled span for the row runs from ``inner + 1`` on the left to its mirror
    image ``2*cmax - inner`` on the right (reflection about ``cmax + 0.5``).
  * Rows whose inner edge already touches the axis (``inner == cmax``) produce an
    empty span and contribute nothing -- this naturally drops the extreme
    top/bottom tips of the arc.
The original arc pixels are cleared to background; only the new filled span keeps
the foreground color.

The latent transformation T is a dict {(r, c): new_color} listing every cell that
changes (arc cells -> background, filled span -> foreground). apply_T copies the
input and overwrites only those masked cells.
"""


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    bg = _background(input_grid)

    # Foreground arc cells (everything that is not background).
    arc = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    T = {}
    if not arc:
        return T

    color = input_grid[arc[0][0]][arc[0][1]]
    cmax = max(c for _, c in arc)

    # Inner (rightmost) arc column per row.
    inner_by_row = {}
    for r, c in arc:
        if r not in inner_by_row or c > inner_by_row[r]:
            inner_by_row[r] = c

    # Clear the original arc to background.
    for r, c in arc:
        T[(r, c)] = bg

    # Fill the closed, reflected span for each arc row.
    for r, inner in inner_by_row.items():
        left = inner + 1
        right = 2 * cmax - inner
        for c in range(left, right + 1):
            if 0 <= c < W:
                T[(r, c)] = color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
