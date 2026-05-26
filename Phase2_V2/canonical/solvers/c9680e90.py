"""Canonical latent-T solver for ARC puzzle c9680e90.

Structure: a full horizontal line of 9s splits the grid into a top half
(containing 5s on background 7) and a bottom half (containing 2s and 6s on
background 7). Each 2 in the bottom has a straight chain of 6s extending from
it in one of the four cardinal directions; that chain is an arrow telling the
2 to slide to the far end of the chain (the chain is erased). Each 5 in the
top mirrors a bottom 2: it is matched to the 2 sharing the same column and the
same distance from the 9-line, and slides by the same horizontal amount while
its vertical motion is reflected across the line. T is the explicit mask of
erased source cells (set to background) and new arrival cells.
"""


def _find_line(grid):
    for r, row in enumerate(grid):
        if all(v == 9 for v in row):
            return r
    return None


def infer_T(grid):
    H = len(grid)
    W = len(grid[0])
    bg = 7
    ln = _find_line(grid)
    if ln is None:
        return {}

    sixset = set((r, c) for r in range(H) for c in range(W) if grid[r][c] == 6)

    # Each bottom 2 follows a straight 6-chain; record its move keyed by
    # (column, distance below the 9-line).
    moves = {}
    for r in range(ln + 1, H):
        for c in range(W):
            if grid[r][c] != 2:
                continue
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (r + dr, c + dc) in sixset:
                    rr, cc, n = r, c, 0
                    while (rr + dr, cc + dc) in sixset:
                        rr += dr
                        cc += dc
                        n += 1
                    moves[(c, r - ln)] = (dr, dc, n)
                    break

    T = {}

    # Erase all bottom markers (2s and 6s), then place each slid 2.
    for r in range(ln + 1, H):
        for c in range(W):
            if grid[r][c] in (2, 6):
                T[(r, c)] = bg
    for (c, dist), (dr, dc, n) in moves.items():
        r = ln + dist
        T[(r + dr * n, c + dc * n)] = 2

    # Erase all top 5s, then place each slid 5 (mirror of its matching 2).
    for r in range(ln):
        for c in range(W):
            if grid[r][c] == 5:
                T[(r, c)] = bg
    for r in range(ln):
        for c in range(W):
            if grid[r][c] != 5:
                continue
            dist = ln - r
            if (c, dist) not in moves:
                continue
            dr, dc, n = moves[(c, dist)]
            ndr = -dr if dc == 0 else 0  # vertical motion reflected across line
            ndc = dc
            T[(r + ndr * n, c + ndc * n)] = 5

    return T


def apply_T(grid, T):
    out = [row[:] for row in grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
