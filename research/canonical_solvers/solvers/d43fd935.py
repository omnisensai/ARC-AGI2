"""Canonical solver for ARC puzzle d43fd935.

Structure: a single solid 2x2 (NxM) block of one "anchor" color sits in the
grid, plus scattered single cells of other colors. Any scattered cell that
lies in the same row-band or column-band as the anchor block shoots a ray of
its own color toward the block, filling the empty (background) gap between
itself and the nearest block edge. Cells not aligned with the block are left
untouched.

infer_T returns a {(r,c): color} latent mask; apply_T overwrites only those.
"""


def _find_block(grid, bg):
    H, W = len(grid), len(grid[0])
    # connected components (4-conn) of each non-bg color; the block is the
    # only component with size > 1 (a filled rectangle).
    seen = [[False] * W for _ in range(H)]
    best = None
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg or seen[r][c]:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            cells = []
            while stack:
                y, x = stack.pop()
                if not (0 <= y < H and 0 <= x < W):
                    continue
                if seen[y][x] or grid[y][x] != color:
                    continue
                seen[y][x] = True
                cells.append((y, x))
                stack.extend([(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)])
            if len(cells) > 1:
                rs = [p[0] for p in cells]
                cs = [p[1] for p in cells]
                best = (min(rs), max(rs), min(cs), max(cs), color, len(cells))
    return best


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    T = {}
    block = _find_block(input_grid, bg)
    if block is None:
        return T
    r0, r1, c0, c1, _bcolor, _ = block

    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg:
                continue
            if r0 <= r <= r1 and (c < c0 or c > c1):
                # same row-band, to the left or right of the block
                if c < c0:
                    rng = range(c + 1, c0)
                else:
                    rng = range(c1 + 1, c)
                for cc in rng:
                    if input_grid[r][cc] == bg:
                        T[(r, cc)] = v
            elif c0 <= c <= c1 and (r < r0 or r > r1):
                # same column-band, above or below the block
                if r < r0:
                    rng = range(r + 1, r0)
                else:
                    rng = range(r1 + 1, r)
                for rr in rng:
                    if input_grid[rr][c] == bg:
                        T[(rr, c)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
