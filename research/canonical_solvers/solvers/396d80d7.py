"""Canonical solver for ARC task 396d80d7.

Rule (same-size):
  The grid contains a single symmetric "figure" drawn over a uniform background.
  The figure uses two non-background colors: an inner "core" color and an outer
  "frame" color. The transformation adds an outer halo around the figure: every
  background cell that touches the figure ONLY diagonally (i.e. all 4 of its
  orthogonal neighbours are background, but at least one of its 4 diagonal
  neighbours is non-background) is filled with the CORE colour. This continues
  the figure's diagonal/diamond outline one step outward.

Canonical infer_T / apply_T form: infer_T computes the latent change mask
{(r,c): core_color}; apply_T copies the input and overwrites only those cells.
"""


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _core_color(grid, bg):
    """Inner colour of the figure = the non-bg colour whose cells are, on
    average, closest to the figure's bounding-box centre."""
    H, W = len(grid), len(grid[0])
    cells = [(r, c, grid[r][c]) for r in range(H) for c in range(W)
             if grid[r][c] != bg]
    if not cells:
        return None
    rs = [r for r, c, v in cells]
    cs = [c for r, c, v in cells]
    cr = (min(rs) + max(rs)) / 2.0
    cc = (min(cs) + max(cs)) / 2.0
    colors = set(v for r, c, v in cells)

    def score(col):
        pts = [(r, c) for r, c, v in cells if v == col]
        avg_dist = sum(abs(r - cr) + abs(c - cc) for r, c in pts) / len(pts)
        return (avg_dist, len(pts))  # closest to centre, then fewest cells

    return min(colors, key=score)


def infer_T(input_grid):
    """Compute the latent change mask {(r, c): new_color}.

    A background cell is marked iff all 4 orthogonal neighbours are background
    and at least one of the 4 diagonal neighbours is non-background.
    """
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    core = _core_color(input_grid, bg)
    T = {}
    if core is None:
        return T

    def is_fig(r, c):
        return 0 <= r < H and 0 <= c < W and input_grid[r][c] != bg

    orth = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    diag = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg:
                continue
            if any(is_fig(r + dr, c + dc) for dr, dc in orth):
                continue
            if any(is_fig(r + dr, c + dc) for dr, dc in diag):
                T[(r, c)] = core
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
