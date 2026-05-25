"""Canonical latent-T solver for ARC puzzle 28a6681f.

Rule (gravity / water settling):
  Color 1 behaves like water; every other non-background (non-0) color is an
  inert wall forming containers. The water cells fall straight down and spread
  horizontally to reach lower positions, blocked by the walls and the grid
  edges, until they reach equilibrium. The output is the input with the water
  removed from its original cells and re-placed at its settled resting cells.

infer_T simulates the settling on the input alone and returns the latent mask
T = {(r,c): 1} of the cells the water finally occupies (plus the originally
occupied cells that must be cleared, encoded as the full new-water set vs the
old-water set). apply_T copies the input, clears the old water, and writes the
settled water.
"""


def _settle(grid, walls):
    """Return the set of cells where the water (color 1) comes to rest."""
    H, W = len(grid), len(grid[0])
    # base grid with water removed; occ marks current water positions
    base = [[(0 if grid[r][c] == 1 else grid[r][c]) for c in range(W)]
            for r in range(H)]
    occ = [[grid[r][c] == 1 for c in range(W)] for r in range(H)]

    def free(r, c):
        return 0 <= r < H and 0 <= c < W and base[r][c] == 0 and not occ[r][c]

    moved = True
    guard = 0
    while moved and guard < 100000:
        moved = False
        guard += 1
        # 1) gravity: every water cell with empty space below falls one step
        for r in range(H - 2, -1, -1):
            for c in range(W):
                if occ[r][c] and free(r + 1, c):
                    occ[r][c] = False
                    occ[r + 1][c] = True
                    moved = True
        if moved:
            continue
        # 2) spreading: a settled water cell that cannot fall flows
        #    horizontally (through free cells in its row) toward the nearest
        #    column where it can drop, then stops to fall next iteration.
        for r in range(H - 1, -1, -1):
            for c in range(W):
                if not occ[r][c] or free(r + 1, c):
                    continue
                for step in (1, -1):
                    cc = c + step
                    done = False
                    while free(r, cc):
                        if free(r + 1, cc):
                            occ[r][c] = False
                            occ[r][cc] = True
                            moved = True
                            done = True
                            break
                        cc += step
                    if done:
                        break
                if moved:
                    break
            if moved:
                break

    return set((r, c) for r in range(H) for c in range(W) if occ[r][c])


def infer_T(input_grid):
    """Latent transformation mask: T[r][c] = 1 where water settles, else None."""
    H, W = len(input_grid), len(input_grid[0])
    # walls = every non-background, non-water color
    walls = set(v for row in input_grid for v in row) - {0, 1}
    settled = _settle(input_grid, walls)
    T = [[None] * W for _ in range(H)]
    # any cell that was water OR becomes water is part of the mask;
    # settled cells -> 1, previously-water cells that are no longer occupied -> 0
    for r in range(H):
        for c in range(W):
            if (r, c) in settled:
                T[r][c] = 1
            elif input_grid[r][c] == 1:
                T[r][c] = 0
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
