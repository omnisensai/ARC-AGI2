"""Canonical solver for ARC puzzle ca8f78db.

Rule: the grid is a doubly-periodic background pattern (a repeating tile with a
vertical period and a horizontal period) that has been partially occluded by
rectangular blocks of a "noise" color (0). The transformation restores the
original pattern by inferring the tile's periods and phase template from the
surviving (non-noise) cells, then repainting only the occluded (noise) cells.

infer_T discovers the periods by consensus over all non-noise cells and returns
a mask giving the correct color for every noise cell; apply_T overwrites only
those masked cells.
"""


def _find_periods(grid, noise):
    """Smallest vertical/horizontal periods consistent with all non-noise cells."""
    H, W = len(grid), len(grid[0])

    def ok_v(p):
        for c in range(W):
            seen = {}
            for r in range(H):
                v = grid[r][c]
                if v == noise:
                    continue
                k = r % p
                if k in seen and seen[k] != v:
                    return False
                seen[k] = v
        return True

    def ok_h(p):
        for r in range(H):
            seen = {}
            for c in range(W):
                v = grid[r][c]
                if v == noise:
                    continue
                k = c % p
                if k in seen and seen[k] != v:
                    return False
                seen[k] = v
        return True

    pr = next(p for p in range(1, H + 1) if ok_v(p))
    pc = next(p for p in range(1, W + 1) if ok_h(p))
    return pr, pc


def infer_T(input_grid, noise=0):
    H, W = len(input_grid), len(input_grid[0])
    pr, pc = _find_periods(input_grid, noise)

    # Consensus template indexed by phase (r % pr, c % pc).
    template = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == noise:
                continue
            template[(r % pr, c % pc)] = v

    # Latent mask: correct color for each occluded (noise) cell.
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == noise:
                key = (r % pr, c % pc)
                if key in template:
                    T[r][c] = template[key]
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
