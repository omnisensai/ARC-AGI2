"""Canonical latent-T solver for ARC puzzle f0100645.

Structure of every pair:
  - Column 0 is a solid wall of color A (left wall).
  - Column W-1 is a solid wall of color B (right wall).
  - The background is the most common interior color (7 in all pairs).
  - Floating objects of color A and color B live in the interior.

Rule: every interior object slides horizontally toward its own wall (A
objects slide left, B objects slide right) as a rigid block, stopping when
it touches the wall or another already-settled same-color object. Objects
are 8-connected (diagonal adjacency keeps a block rigid). Objects nearest
the wall settle first so farther ones stack behind them.

infer_T computes, from the input alone, the latent mask of cell color
changes produced by this sliding; apply_T overwrites only those cells.
"""


def _components(grid, color, H, W, cols):
    """8-connected components of `color` restricted to interior `cols`."""
    cols = set(cols)
    seen = set()
    comps = []
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
          (0, 1), (1, -1), (1, 0), (1, 1)]
    for r in range(H):
        for c in sorted(cols):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if (y, x) in seen:
                        continue
                    if not (0 <= y < H and x in cols):
                        continue
                    if grid[y][x] != color:
                        continue
                    seen.add((y, x))
                    cells.append((y, x))
                    for dy, dx in nb:
                        stack.append((y + dy, x + dx))
                comps.append(cells)
    return comps


def _slide(objs, direction, W):
    """Slide each object toward a wall; return final cell lists.

    direction = -1 slides left (toward col 1), +1 slides right (toward W-2).
    Objects closest to the target wall settle first; later objects stop on
    contact with already-settled cells or the wall.
    """
    if direction == -1:
        objs = sorted(objs, key=lambda ob: min(c for _, c in ob))
    else:
        objs = sorted(objs, key=lambda ob: -max(c for _, c in ob))
    placed = set()
    finals = []
    for ob in objs:
        shift = 0
        while True:
            ns = shift + direction
            cand = [(r, c + ns) for r, c in ob]
            if any(c < 1 or c > W - 2 or (r, c) in placed for r, c in cand):
                break
            shift = ns
        fin = [(r, c + shift) for r, c in ob]
        placed.update(fin)
        finals.append(fin)
    return finals


def infer_T(input_grid):
    """Infer the latent transformation mask {(r, c): new_color}."""
    H = len(input_grid)
    W = len(input_grid[0])

    # Walls define the two object colors and the slide direction.
    A = input_grid[0][0]          # left wall color
    B = input_grid[0][W - 1]      # right wall color

    # Background = most common interior color.
    counts = {}
    for r in range(H):
        for c in range(1, W - 1):
            v = input_grid[r][c]
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get) if counts else 0

    cols = range(1, W - 1)
    T = {}

    # Clear every current interior object cell back to background.
    for r in range(H):
        for c in cols:
            if input_grid[r][c] in (A, B) and input_grid[r][c] != bg:
                T[(r, c)] = bg

    # Slide A objects left, B objects right; paint their settled positions.
    for fin in _slide([list(ob) for ob in _components(input_grid, A, H, W, cols)], -1, W):
        for r, c in fin:
            T[(r, c)] = A
    for fin in _slide([list(ob) for ob in _components(input_grid, B, H, W, cols)], +1, W):
        for r, c in fin:
            T[(r, c)] = B

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
