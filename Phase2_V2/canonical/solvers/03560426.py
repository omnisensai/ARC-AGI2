def _find_blocks(g):
    """Connected solid-color rectangular blocks on a 0 background."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    blocks = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and not seen[r][c]:
                color = g[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if seen[rr][cc] or g[rr][cc] != color:
                        continue
                    seen[rr][cc] = True
                    cells.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((rr + dr, cc + dc))
                rs = [x[0] for x in cells]
                cs = [x[1] for x in cells]
                blocks.append((color, min(rs), max(rs), min(cs), max(cs)))
    return blocks


def infer_T(input_grid):
    """Latent mask {(r,c): new_color}.

    The input holds several solid rectangular blocks spread out along the
    bottom row. Ordering them left to right, the transformation restacks them
    into a diagonal staircase anchored at the top-left corner: each block's
    top-left corner is placed on the previous block's bottom-right corner
    (a one-cell overlap), with later blocks drawn over earlier ones. The
    original block cells are cleared to background.
    """
    H, W = len(input_grid), len(input_grid[0])
    blocks = sorted(_find_blocks(input_grid), key=lambda b: b[3])
    T = {}
    # clear every original block cell to background
    for color, r0, r1, c0, c1 in blocks:
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                T[(r, c)] = 0
    # redraw the staircase
    cr, cc = 0, 0
    for color, r0, r1, c0, c1 in blocks:
        h = r1 - r0 + 1
        w = c1 - c0 + 1
        for r in range(cr, cr + h):
            for c in range(cc, cc + w):
                if 0 <= r < H and 0 <= c < W:
                    T[(r, c)] = color
        cr = cr + h - 1
        cc = cc + w - 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
