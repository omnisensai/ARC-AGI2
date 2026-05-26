"""Canonical solver for ARC puzzle 891232d6.

Rule (beam / staircase bounce):
  Each cell with color 6 in the grid is a "launcher". From each launcher a
  beam of color 2 travels straight UP. Whenever the beam runs into a
  horizontal bar of 7s from below it "bounces":
    - the bar cell hit is recolored 8,
    - the cell just below it (the entry corner) becomes 4,
    - the beam runs RIGHT along the row immediately below the bar (color 2)
      until it passes the bar's right end,
    - at the column one past the bar's right end it places 3 (the turn) and
      then resumes traveling UP from the bar's own row.
  The beam terminates with a 6 either when it leaves the top of the grid
  (the top-most cell becomes 6) or when the rightward bounce path is blocked
  by another 7 (the entry corner becomes 6 instead of 4 and the beam stops).

T is a latent mask: a dict {(r,c): new_color} of cells the beam overwrites.
apply_T copies the input and writes only those masked cells.
"""


def infer_T(grid):
    H, W = len(grid), len(grid[0])
    T = {}  # (r, c) -> new color

    launchers = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == 6]

    for mr, mc in launchers:
        col = mc
        row = mr - 1          # first cell above the launcher
        local = {}            # provisional marks for this beam
        edge_exit = False

        while True:
            if row < 0:
                edge_exit = True
                break

            if grid[row][col] == 7:
                # Hit a horizontal bar at this row; find its extent.
                br = row
                cl = col
                while cl - 1 >= 0 and grid[br][cl - 1] == 7:
                    cl -= 1
                cr = col
                while cr + 1 < W and grid[br][cr + 1] == 7:
                    cr += 1
                corner_r = br + 1

                # Can the beam turn and run right under the bar?
                blocked = cr + 1 >= W
                if not blocked:
                    for cc in range(col + 1, cr + 2):
                        if grid[corner_r][cc] == 7:
                            blocked = True
                            break

                if blocked:
                    local[(corner_r, col)] = 6
                    break

                # Commit the bounce.
                local[(br, col)] = 8
                local[(corner_r, col)] = 4
                for cc in range(col + 1, cr + 1):
                    local[(corner_r, cc)] = 2
                local[(corner_r, cr + 1)] = 3
                col = cr + 1
                row = br          # resume upward from the bar's own row
                continue
            else:
                local[(row, col)] = 2
                row -= 1

        if edge_exit:
            # Beam left the top of the grid: topmost cell becomes 6.
            local[(0, col)] = 6

        T.update(local)

    return T


def apply_T(grid, T):
    out = [row[:] for row in grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
