"""Canonical latent-T solver for ARC puzzle c61be7dc.

Structure of every input:
  * A "channel": two parallel full separator lines of color 0 (either two whole
    columns -> vertical channel, or two whole rows -> horizontal channel).
  * A perpendicular separator line of 0 running through the middle of the grid,
    interrupted in the channel by a connected shape of 5s (an "arrow").

Rule (read off ALL pairs):
  * Let N = number of 5 cells.  The arrow is straightened into a single straight
    line of 5s of length N, running PARALLEL to the channel, centred on the
    perpendicular line.
  * The two parallel separators collapse inward to hug that 5-line (one cell on
    each side).
  * The perpendicular separator line is redrawn as a full line of 0, with the
    5-line crossing it.
  * Everything else in the channel region becomes background.

infer_T builds the intended output from the input structure alone and returns a
sparse mask {(r,c): new_color} of the cells that differ from the input; apply_T
copies the input and overwrites only those cells.
"""


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _intended_output(grid):
    H, W = len(grid), len(grid[0])
    bg = _background(grid)

    fives = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == 5]
    if not fives:
        return [row[:] for row in grid]
    N = len(fives)
    rs = [r for r, _ in fives]
    cs = [c for _, c in fives]
    # centre of the arrow shape -> position of the perpendicular separator line
    crow = (min(rs) + max(rs)) // 2
    ccol = (min(cs) + max(cs)) // 2

    # find the two parallel full-0 separators forming the channel
    full_rows = [r for r in range(H) if all(grid[r][c] == 0 for c in range(W))]
    full_cols = [c for c in range(W) if all(grid[r][c] == 0 for r in range(H))]

    out = [[bg] * W for _ in range(H)]

    if len(full_cols) >= 2:
        # vertical channel: 5-line runs vertically (parallel to the channel)
        ca, cb = min(full_cols), max(full_cols)
        mid = (ca + cb) // 2
        # collapse parallel separators to hug the centre line
        for r in range(H):
            out[r][mid - 1] = 0
            out[r][mid + 1] = 0
        # perpendicular separator line (full row through the shape centre)
        for c in range(W):
            out[crow][c] = 0
        # straightened 5-line, length N, centred on the perpendicular line
        half = N // 2
        for r in range(crow - half, crow - half + N):
            if 0 <= r < H:
                out[r][mid] = 5
    elif len(full_rows) >= 2:
        # horizontal channel: 5-line runs horizontally
        ra, rb = min(full_rows), max(full_rows)
        mid = (ra + rb) // 2
        for c in range(W):
            out[mid - 1][c] = 0
            out[mid + 1][c] = 0
        # perpendicular separator line (full column through the shape centre)
        for r in range(H):
            out[r][ccol] = 0
        half = N // 2
        for c in range(ccol - half, ccol - half + N):
            if 0 <= c < W:
                out[mid][c] = 5
    else:
        return [row[:] for row in grid]

    return out


def infer_T(input_grid):
    """Return latent mask {(r,c): new_color} of cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    target = _intended_output(input_grid)
    T = {}
    for r in range(H):
        for c in range(W):
            if target[r][c] != input_grid[r][c]:
                T[(r, c)] = target[r][c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
