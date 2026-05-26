"""Canonical solver for ARC puzzle fe45cba4.

Rule (inferred from input structure):
  - Background is the most common color.
  - For each non-background color there may be one or two connected
    components (8-connectivity). A color with a single component is left
    untouched.
  - When a color has two components, one of them touches the right edge of
    the grid (the "anchor"); the other (typically touching the left edge) is
    an auxiliary "key" that only contributes its cell count. The total number
    of colored cells of that color is conserved and reshaped into a SOLID
    rectangle that keeps the anchor's row span, is flush against the right
    edge, and has width = total_cells // number_of_rows. All original cells of
    that color are cleared and the solid rectangle is painted.
"""


def _components(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    neigh = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                seen[r][c] = True
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in neigh:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] and grid[nr][nc] == color:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append((color, cells))
    return comps


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Group components by color.
    by_color = {}
    for color, cells in _components(input_grid, bg):
        by_color.setdefault(color, []).append(cells)

    T = {}  # latent mask: {(r,c): new_color}

    for color, clist in by_color.items():
        if len(clist) != 2:
            continue  # single (or odd) component: leave untouched

        total = sum(len(cells) for cells in clist)

        # Anchor = component touching the right edge.
        anchor = None
        for cells in clist:
            if any(c == W - 1 for _, c in cells):
                anchor = cells
                break
        if anchor is None:
            continue

        rs = [r for r, _ in anchor]
        r0, r1 = min(rs), max(rs)
        nrows = r1 - r0 + 1
        if total % nrows != 0:
            continue
        width = total // nrows

        # Clear all existing cells of this color.
        for cells in clist:
            for (r, c) in cells:
                T[(r, c)] = bg

        # Paint solid rectangle flush against the right edge, same rows.
        c1 = W - 1
        c0 = c1 - width + 1
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if 0 <= c < W:
                    T[(r, c)] = color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
