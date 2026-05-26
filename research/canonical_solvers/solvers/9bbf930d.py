"""Canonical latent-T solver for ARC puzzle 9bbf930d.

Structure of every input
-------------------------
Column 0 is a solid run of 6s (a "ball reservoir") and column 1 is a 7-spacer.
The interior is a stack of horizontal colored *bars* on the even rows
(0, 2, 4, ...) separated by gap rows (the odd rows). The bars and their right
side decorations form 1-cell-wide pipe/maze corridors in the 7 cells.

Rule
----
Whenever two vertically adjacent bars (rows r-1 and r+1) share the SAME color,
the gap row r between them becomes an entry: the 6 ball stored at (r,0) is
released. It rolls rightward through the open (7) corridor:
  * it travels straight while the cell ahead is open,
  * when blocked it turns into the single open perpendicular corridor and
    continues,
  * it STOPS (and deposits the 6) when it runs off a grid edge, when it reaches
    a fork (both perpendiculars open -> a T junction), or when it is stopped by
    a bar cell and the only available turn would send it backwards (leftwards).
The released cell (r,0) is cleared to 7, and a 6 is written at the stop cell.

infer_T computes the set of changed cells (the latent mask); apply_T copies the
input and overwrites only those cells.
"""

from collections import Counter


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    def bar_color(r):
        cnt = Counter(v for v in input_grid[r][2:] if v != 7)
        return cnt.most_common(1)[0][0] if cnt else None

    # dominant color of each (even) bar row
    bcol = {r: bar_color(r) for r in range(0, H, 2)}

    def is_bar_cell(r, c):
        return (0 <= r < H and r % 2 == 0 and bcol.get(r) is not None
                and input_grid[r][c] == bcol[r])

    def is_open(r, c):
        return 0 <= r < H and 0 <= c < W and input_grid[r][c] == 7

    # entry gap-rows: odd rows whose two bounding bars share a color
    entries = [r for r in range(1, H, 2)
               if 0 <= r - 1 and r + 1 < H
               and bar_color(r - 1) is not None
               and bar_color(r - 1) == bar_color(r + 1)]

    def roll(start_row):
        r, c = start_row, 1
        d = (0, 1)                     # start moving right
        visited = {(r, c)}
        while True:
            nr, nc = r + d[0], c + d[1]
            if is_open(nr, nc) and (nr, nc) not in visited:
                r, c = nr, nc
                visited.add((r, c))
                continue
            # ran off the edge -> stop
            if not (0 <= nr < H and 0 <= nc < W):
                return (r, c)
            blocked_by_bar = is_bar_cell(nr, nc)
            # perpendicular turn candidates
            perps = [(1, 0), (-1, 0)] if d[0] == 0 else [(0, 1), (0, -1)]
            opts = [pd for pd in perps
                    if is_open(r + pd[0], c + pd[1])
                    and (r + pd[0], c + pd[1]) not in visited]
            if len(opts) == 1:
                pd = opts[0]
                # stopped by a bar with only a backward (leftward) turn -> stop
                if blocked_by_bar and pd[1] == -1:
                    return (r, c)
                d = pd
                r, c = r + pd[0], c + pd[1]
                visited.add((r, c))
                continue
            # fork (T junction) or dead end -> stop
            return (r, c)

    T = {}
    for sr in entries:
        T[(sr, 0)] = 7              # release the ball from the reservoir
        er, ec = roll(sr)
        T[(er, ec)] = 6             # deposit the ball where it stops
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
