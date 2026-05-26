"""Canonical solver for ARC puzzle 17829a00.

Rule
----
The grid has a solid top border row (color = top color) and a solid bottom
border row (color = bottom color). Scattered through the interior are
connected shapes drawn either in the top color or the bottom color (8-connected
components).

Each top-colored shape slides straight UP until it abuts the top border
(its topmost cell lands on row 1), preserving its exact shape and columns.
Each bottom-colored shape slides straight DOWN until it abuts the bottom border
(its bottommost cell lands on row H-2), preserving its exact shape and columns.

Exception: a bottom-colored shape that is a single vertical bar whose required
slide distance is smaller than the bar's own length does not translate; instead
it stays anchored at its top cell and grows downward, filling every cell from
its original top down to the bottom border (an "icicle" reaching the wall).

The transformation T is the explicit set of interior cells that end up colored
(top or bottom color) after this motion; apply_T copies the input borders and
clears the interior, then paints the masked cells.
"""


def _components(grid, color, H, W):
    """8-connected components of `color` over `grid`, each a sorted cell list."""
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if (y, x) in seen or not (0 <= y < H and 0 <= x < W):
                        continue
                    if grid[y][x] != color:
                        continue
                    seen.add((y, x))
                    cells.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy or dx:
                                stack.append((y + dy, x + dx))
                out.append(sorted(cells))
    return out


def infer_T(input_grid):
    """Return the latent mask T as a dict {(r, c): color} of interior cells
    that should be painted after every shape has moved to its wall."""
    H, W = len(input_grid), len(input_grid[0])
    top = input_grid[0][0]
    bot = input_grid[H - 1][0]

    # Interior only (ignore the two border rows when finding shapes).
    interior = [
        [input_grid[r][c] if 1 <= r <= H - 2 else 7 for c in range(W)]
        for r in range(H)
    ]

    T = {}

    # Top-colored shapes slide up so their topmost cell reaches row 1.
    for cells in _components(interior, top, H, W):
        rows = [y for y, _ in cells]
        shift = min(rows) - 1
        for y, x in cells:
            T[(y - shift, x)] = top

    # Bottom-colored shapes slide down so their bottommost cell reaches row H-2.
    for cells in _components(interior, bot, H, W):
        cols = set(x for _, x in cells)
        rows = [y for y, _ in cells]
        minr, maxr = min(rows), max(rows)
        length = maxr - minr + 1
        slide = (H - 2) - maxr
        is_vbar = len(cols) == 1 and length == len(cells)

        if is_vbar and slide < length:
            # Icicle: anchored at its top, grow down to the bottom wall.
            x = next(iter(cols))
            for y in range(minr, H - 1):
                T[(y, x)] = bot
        else:
            for y, x in cells:
                T[(y + slide, x)] = bot

    return T


def apply_T(input_grid, T):
    """Copy borders, clear interior to background (7), then paint masked cells."""
    H, W = len(input_grid), len(input_grid[0])
    top = input_grid[0][0]
    bot = input_grid[H - 1][0]

    out = [[7] * W for _ in range(H)]
    out[0] = [top] * W
    out[H - 1] = [bot] * W

    for (r, c), color in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
