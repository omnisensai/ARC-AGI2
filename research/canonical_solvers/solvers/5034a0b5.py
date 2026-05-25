"""Canonical solver for ARC puzzle 5034a0b5.

Rule: the grid is a frame whose four edges each carry a distinct color (read from
the middle of the top/bottom/left/right border rows/columns). The interior is a
background of a single color, sprinkled with non-background "marker" cells. Each
marker whose color equals one of the four border colors moves one step toward the
matching border (top color -> up, bottom -> down, left -> left, right -> right),
unless that step would land on the frame (in which case it stays). Markers whose
color matches no border color stay where they are. The mask T records the cleared
old positions and the new colored positions.
"""


def _border_colors(grid):
    H, W = len(grid), len(grid[0])
    # interior background = most common interior color
    counts = {}
    for r in range(1, H - 1):
        for c in range(1, W - 1):
            counts[grid[r][c]] = counts.get(grid[r][c], 0) + 1
    bg = max(counts, key=counts.get) if counts else grid[1][1]
    # edge colors read from the middle of each border (avoids corner frame color)
    top = grid[0][W // 2]
    bot = grid[H - 1][W // 2]
    left = grid[H // 2][0]
    right = grid[H // 2][W - 1]
    return bg, top, bot, left, right


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg, top, bot, left, right = _border_colors(input_grid)

    dir_of = {}  # color -> (dr, dc) step toward its matching border
    for color, d in ((top, (-1, 0)), (bot, (1, 0)),
                     (left, (0, -1)), (right, (0, 1))):
        dir_of.setdefault(color, d)

    # T maps cell -> new color; cleared cells map to bg.
    T = {}
    for r in range(1, H - 1):
        for c in range(1, W - 1):
            v = input_grid[r][c]
            if v == bg:
                continue
            if v in dir_of:
                dr, dc = dir_of[v]
                nr, nc = r + dr, c + dc
                if 1 <= nr <= H - 2 and 1 <= nc <= W - 2:
                    # move: clear old, set new
                    if (r, c) not in T:
                        T[(r, c)] = bg
                    T[(nr, nc)] = v
                # else: blocked by frame, stays -> no change recorded
            # markers matching no border color stay -> no change
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
