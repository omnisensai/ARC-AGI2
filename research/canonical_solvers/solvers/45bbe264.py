def infer_T(input_grid):
    """Each non-zero marker (r,c,color) projects a full-column line and a
    full-row line of its color. Returns a dict {(r,c): new_color} mask:
      - the marker's own cell keeps its color,
      - a cell crossed by both a row-line and a column-line becomes 2,
      - any other line cell takes the color of the line passing through it."""
    H, W = len(input_grid), len(input_grid[0])
    markers = [(r, c, input_grid[r][c])
               for r in range(H) for c in range(W) if input_grid[r][c] != 0]

    contribs = {}
    for (mr, mc, color) in markers:
        for r in range(H):
            contribs.setdefault((r, mc), []).append(("V", color, mr, mc))
        for c in range(W):
            contribs.setdefault((mr, c), []).append(("H", color, mr, mc))

    T = {}
    for (r, c), items in contribs.items():
        own = [color for (k, color, mr, mc) in items if (mr, mc) == (r, c)]
        has_h = any(k == "H" for (k, color, mr, mc) in items)
        has_v = any(k == "V" for (k, color, mr, mc) in items)
        if own:
            T[(r, c)] = own[0]
        elif has_h and has_v:
            T[(r, c)] = 2
        else:
            T[(r, c)] = items[0][1]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
