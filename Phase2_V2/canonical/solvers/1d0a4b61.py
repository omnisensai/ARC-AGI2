from collections import Counter


def _find_period(grid, H, W, noise=0):
    """Smallest vertical/horizontal periods compatible with all non-noise cells."""
    def vok(py):
        for r in range(H):
            for c in range(W):
                rr = r + py
                if rr < H:
                    a, b = grid[r][c], grid[rr][c]
                    if a != noise and b != noise and a != b:
                        return False
        return True

    def hok(px):
        for r in range(H):
            for c in range(W):
                cc = c + px
                if cc < W:
                    a, b = grid[r][c], grid[r][cc]
                    if a != noise and b != noise and a != b:
                        return False
        return True

    py = next((p for p in range(1, H + 1) if vok(p)), H)
    px = next((p for p in range(1, W + 1) if hok(p)), W)
    return py, px


def infer_T(input_grid):
    """Latent mask: reconstruct the noise (0) cells of a periodic tiling.

    Detects the grid's vertical/horizontal periods from the undamaged cells,
    builds a consensus tile by majority vote over every position congruent
    modulo the period, and produces a {(r,c): color} mask for each 0 cell.
    """
    H, W = len(input_grid), len(input_grid[0])
    noise = 0
    py, px = _find_period(input_grid, H, W, noise)

    votes = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == noise:
                continue
            votes.setdefault((r % py, c % px), Counter())[v] += 1
    tile = {k: cnt.most_common(1)[0][0] for k, cnt in votes.items()}

    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == noise:
                key = (r % py, c % px)
                if key in tile:
                    T[(r, c)] = tile[key]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
