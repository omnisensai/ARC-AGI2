"""Canonical solver for ARC puzzle 31adaf00.

Rule: the grid is 5s scattered on a 0 background. Find every maximal solid
square block of background (0) cells of side >= 2. Selecting from the largest
squares to the smallest (greedily, skipping any square that overlaps an
already-selected one), repaint the cells of the selected squares with color 1.
Squares may touch diagonally/edge-to-edge but never share a cell.
"""


def _all_zero(grid, r, c, n):
    return all(grid[rr][cc] == 0
               for rr in range(r, r + n)
               for cc in range(c, c + n))


def _cells(n, r, c):
    return {(rr, cc) for rr in range(r, r + n) for cc in range(c, c + n)}


def infer_T(input_grid):
    """Compute the latent mask: cells of the chosen empty squares -> color 1."""
    H, W = len(input_grid), len(input_grid[0])

    # Enumerate every all-zero square block with side >= 2.
    squares = []
    for n in range(2, min(H, W) + 1):
        for r in range(H - n + 1):
            for c in range(W - n + 1):
                if _all_zero(input_grid, r, c, n):
                    squares.append((n, r, c))

    # Greedy selection: largest first, skip squares overlapping a chosen one.
    squares.sort(key=lambda s: (-s[0], s[1], s[2]))
    chosen = set()
    for n, r, c in squares:
        cells = _cells(n, r, c)
        if cells & chosen:
            continue
        chosen |= cells

    T = [[None] * W for _ in range(H)]
    for r, c in chosen:
        T[r][c] = 1
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
