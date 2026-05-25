def infer_T(input_grid):
    """Latent mask: dict {(r,c): new_color} for cells overwritten by the magnet rule.

    Each row holds exactly two non-zero cells. Certain "magnet" color pairs
    ({4,7} and {1,8}) attract: the right cell slides left until it sits
    immediately to the right of the left (anchor) cell. All other pairs are
    inert and stay put.
    """
    H, W = len(input_grid), len(input_grid[0])
    MAGNETS = [{4, 7}, {1, 8}]
    T = {}
    for r in range(H):
        nz = [(c, input_grid[r][c]) for c in range(W) if input_grid[r][c] != 0]
        if len(nz) != 2:
            continue
        (c1, v1), (c2, v2) = nz
        if {v1, v2} not in MAGNETS:
            continue
        # left cell is the anchor; right cell moves adjacent to its right
        (lc, lv), (rc, rv) = sorted(nz)
        new_rc = lc + 1
        if new_rc == rc:
            continue  # already adjacent, no change
        # clear the old right-cell position, write the moved cell
        T[(r, rc)] = 0
        T[(r, new_rc)] = rv
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
