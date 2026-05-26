from collections import Counter


def _sep_color(grid):
    """The dominant non-zero color = the separator/gridline color."""
    c = Counter()
    for row in grid:
        for v in row:
            c[v] += 1
    c.pop(0, None)
    return c.most_common(1)[0][0]


def _sep_lines(grid, s):
    """Rows/cols that are (mostly) made of the separator color = gridlines."""
    H, W = len(grid), len(grid[0])
    seprows = [r for r in range(H) if sum(1 for v in grid[r] if v == s) > W // 2]
    sepcols = [c for c in range(W) if sum(1 for r in range(H) if grid[r][c] == s) > H // 2]
    return seprows, sepcols


def _compartment(r, c, seprows, sepcols):
    """Index (band-row, band-col) of the grid compartment a cell falls in."""
    i = sum(1 for sr in seprows if sr < r)
    j = sum(1 for sc in sepcols if sc < c)
    return (i, j)


def infer_T(input_grid):
    """
    Latent mask: {(r,c): new_color}.

    Background (0) cells, flood-filled with separator cells acting as walls,
    form connected regions. Where the gridlines are intact a region stays
    inside a single compartment -> recolor 3. Where a gridline has a gap, two
    or more compartments merge into one region -> recolor 4.
    """
    H, W = len(input_grid), len(input_grid[0])
    s = _sep_color(input_grid)
    seprows, sepcols = _sep_lines(input_grid, s)

    seen = [[False] * W for _ in range(H)]
    T = {}
    for sr in range(H):
        for sc in range(W):
            if input_grid[sr][sc] == 0 and not seen[sr][sc]:
                stack = [(sr, sc)]
                comp = []
                while stack:
                    r, c = stack.pop()
                    if not (0 <= r < H and 0 <= c < W):
                        continue
                    if seen[r][c] or input_grid[r][c] != 0:
                        continue
                    seen[r][c] = True
                    comp.append((r, c))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((r + dr, c + dc))
                comps = {_compartment(r, c, seprows, sepcols) for r, c in comp}
                color = 3 if len(comps) == 1 else 4
                for r, c in comp:
                    T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
