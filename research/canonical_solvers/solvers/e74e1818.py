def infer_T(input_grid):
    """Infer a latent transformation mask.

    Each non-background color forms a single object stacked vertically.
    The transformation mirrors every such object top-to-bottom within its
    own row-extent (bounding rows), leaving columns unchanged. Background
    (0) is untouched.

    T is returned as a dict {(r, c): new_color} listing only the cells that
    differ after the per-color vertical flip.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    # Group all non-background cells by color.
    cells_by_color = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0:
                cells_by_color.setdefault(v, []).append((r, c))

    # Build the flipped layout per color, then derive the change mask.
    new_color = {}  # (r, c) -> color after flip
    cleared = set()  # cells that held a color in the input
    for color, cells in cells_by_color.items():
        rows = [r for r, _ in cells]
        r0, r1 = min(rows), max(rows)
        for (r, c) in cells:
            cleared.add((r, c))
            nr = r0 + r1 - r  # mirror row within the object's row-extent
            new_color[(nr, c)] = color

    T = {}
    for r in range(H):
        for c in range(W):
            cur = input_grid[r][c]
            if (r, c) in new_color:
                if new_color[(r, c)] != cur:
                    T[(r, c)] = new_color[(r, c)]
            elif (r, c) in cleared:
                # Held a color in the input but nothing maps here now.
                if cur != 0:
                    T[(r, c)] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
