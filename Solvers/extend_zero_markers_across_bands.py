"""
Puzzle: 855e0971
Rule name: extend_zero_markers_across_bands

Transformation rule:
Within each uniform-colored band (rows or columns), extend every zero marker into a full perpendicular line spanning that band's width.

Validation: all 5/5 pairs (training + test) of the source puzzle pass.
Source: agent-generated R1 code (Claude general-purpose, seed prompt v1).
Judge consensus: 3/5 LLM judges produced this exact rule name.
"""
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    def row_uniform_color(r):
        vals = set(v for v in grid[r] if v != 0)
        return vals.pop() if len(vals) == 1 else None

    def col_uniform_color(c):
        vals = set(grid[r][c] for r in range(H) if grid[r][c] != 0)
        return vals.pop() if len(vals) == 1 else None

    row_colors = [row_uniform_color(r) for r in range(H)]
    col_colors = [col_uniform_color(c) for c in range(W)]

    rows_uniform = all(rc is not None for rc in row_colors)
    cols_uniform = all(cc is not None for cc in col_colors)

    horizontal = rows_uniform and not cols_uniform
    if not horizontal and not (cols_uniform and not rows_uniform):
        horizontal = len(set(row_colors)) >= len(set(col_colors))

    h_bands = []
    if rows_uniform:
        start = 0
        for r in range(1, H):
            if row_colors[r] != row_colors[start]:
                h_bands.append((start, r - 1, row_colors[start]))
                start = r
        h_bands.append((start, H - 1, row_colors[start]))

    v_bands = []
    if cols_uniform:
        start = 0
        for c in range(1, W):
            if col_colors[c] != col_colors[start]:
                v_bands.append((start, c - 1, col_colors[start]))
                start = c
        v_bands.append((start, W - 1, col_colors[start]))

    zeros = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == 0]

    out = [row[:] for row in grid]

    if horizontal:
        for r, c in zeros:
            for s, e, col in h_bands:
                if s <= r <= e:
                    out[r][c] = col
                    break
        for r, c in zeros:
            for s, e, col in h_bands:
                if s <= r <= e:
                    for rr in range(s, e + 1):
                        out[rr][c] = 0
                    break
    else:
        for r, c in zeros:
            for s, e, col in v_bands:
                if s <= c <= e:
                    out[r][c] = col
                    break
        for r, c in zeros:
            for s, e, col in v_bands:
                if s <= c <= e:
                    for cc in range(s, e + 1):
                        out[r][cc] = 0
                    break

    return out
