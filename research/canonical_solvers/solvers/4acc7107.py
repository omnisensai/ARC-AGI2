from collections import deque


def _components(grid):
    """Connected components (8-connectivity) of non-zero cells, grouped by color."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and not seen[r][c]:
                color = grid[r][c]
                q = deque([(r, c)])
                seen[r][c] = True
                cells = []
                while q:
                    cr, cc = q.popleft()
                    cells.append((cr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if (0 <= nr < H and 0 <= nc < W and not seen[nr][nc]
                                    and grid[nr][nc] == color):
                                seen[nr][nc] = True
                                q.append((nr, nc))
                comps.append((color, cells))
    return comps


def _bbox(cells):
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _norm(cells):
    """Cells translated so the bounding box starts at (0, 0)."""
    r0 = min(r for r, c in cells)
    c0 = min(c for r, c in cells)
    return [(r - r0, c - c0) for r, c in cells]


def infer_T(input_grid):
    """Latent transformation mask: dict {(r, c): new_color}.

    The grid holds two colors, each with two objects. The objects are relocated
    into two vertical columns (one per color):
      - The color whose objects reach the smaller leftmost column anchors the
        left column at col 0; the other color anchors the right column just past
        the left column's width (1 empty separator column).
      - Within each color the leftmost input object drops to the bottom band
        (its bottom edge at the last row), and the rightmost input object stacks
        above it with exactly one empty row of gap. Both are left-anchored to the
        column. Original object cells are cleared.
    """
    H, W = len(input_grid), len(input_grid[0])
    comps = _components(input_grid)
    by_color = {}
    for color, cells in comps:
        by_color.setdefault(color, []).append(cells)

    T = {}
    if len(by_color) != 2:
        return T

    # Clear every original foreground cell; objects are relocated.
    for color, cells in comps:
        for (r, c) in cells:
            T[(r, c)] = 0

    def min_left(col):
        return min(_bbox(c)[1] for c in by_color[col])

    left_color, right_color = sorted(by_color.keys(), key=min_left)
    left_width = max(_bbox(c)[3] - _bbox(c)[1] + 1 for c in by_color[left_color])
    column_anchor = {left_color: 0, right_color: left_width + 1}

    for color in (left_color, right_color):
        objs = by_color[color]
        if len(objs) != 2:
            continue
        # Leftmost input object -> bottom band; rightmost input object -> top.
        bot_obj, top_obj = sorted(objs, key=lambda c: _bbox(c)[1])
        base_col = column_anchor[color]

        bot_cells = _norm(bot_obj)
        bot_h = max(r for r, c in bot_cells) + 1
        bot_top = H - bot_h
        for (r, c) in bot_cells:
            T[(bot_top + r, base_col + c)] = color

        top_cells = _norm(top_obj)
        top_h = max(r for r, c in top_cells) + 1
        # One empty row of gap between the top object's bottom and the bottom object's top.
        top_top = (bot_top - 2) - top_h + 1
        for (r, c) in top_cells:
            T[(top_top + r, base_col + c)] = color

    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the cells named by the mask."""
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
