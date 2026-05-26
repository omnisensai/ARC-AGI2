"""Canonical latent-T solver for ARC puzzle d687bc17.

Structure: the grid has a rectangular border frame whose four walls each have a
distinct color (top row, bottom row, left column, right column; corners are
background 0). The interior holds scattered single colored cells. Each interior
cell whose color matches one of the four wall colors slides straight (along the
axis perpendicular to that wall) until it rests in the cell immediately inside
that wall, keeping its other coordinate. Interior cells whose color matches no
wall vanish. infer_T produces the mask of cell changes (clear the source cells
and the destinations get the moved colors); apply_T overwrites only those cells.
"""


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    # background = most common color overall
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Identify the four wall colors from border edges (excluding corners).
    top = input_grid[0][1]
    bot = input_grid[H - 1][1]
    left = input_grid[1][0]
    right = input_grid[1][W - 1]

    # Latent mask: dict {(r,c): new_color}. None of the wall cells change.
    T = {}

    for r in range(1, H - 1):
        for c in range(1, W - 1):
            color = input_grid[r][c]
            if color == bg:
                continue
            # clear the source cell
            T[(r, c)] = bg
            # determine destination wall by matching color
            dest = None
            if color == top:
                dest = (1, c)
            elif color == bot:
                dest = (H - 2, c)
            elif color == left:
                dest = (r, 1)
            elif color == right:
                dest = (r, W - 2)
            if dest is not None:
                T[dest] = color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
