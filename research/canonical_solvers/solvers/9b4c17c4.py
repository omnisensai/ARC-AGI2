from collections import deque


def infer_T(input_grid):
    """Infer a latent transformation mask.

    The grid is split into two regions by background color: an 8-background
    region and a 1-background region (divided by a straight horizontal or
    vertical line). Each region contains one or more red (2) shapes. Every
    shape slides HORIZONTALLY within its region until it touches the region
    edge: shapes in the 8-region slide to that region's LEFT column, shapes
    in the 1-region slide to that region's RIGHT column. Rows are preserved.

    T is a dict {(r,c): ('bg', region_color)} for cleared old shape cells and
    {(r,c): ('shape', 2)} for the new shape positions.
    """
    H, W = len(input_grid), len(input_grid[0])
    SHAPE = 2

    # Assign every cell to a region color (8 or 1). Background cells define
    # their region directly; shape cells inherit the region of the surrounding
    # background via BFS.
    region = [[None] * W for _ in range(H)]
    dq = deque()
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] in (8, 1):
                region[r][c] = input_grid[r][c]
                dq.append((r, c))
    while dq:
        r, c = dq.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and region[nr][nc] is None:
                region[nr][nc] = region[r][c]
                dq.append((nr, nc))

    # Column extent of each region.
    cols = {8: [W, -1], 1: [W, -1]}
    for r in range(H):
        for c in range(W):
            rc = region[r][c]
            if rc in cols:
                if c < cols[rc][0]:
                    cols[rc][0] = c
                if c > cols[rc][1]:
                    cols[rc][1] = c

    # Connected components of shape color (4-connectivity).
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == SHAPE and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < H and 0 <= nc < W
                                and input_grid[nr][nc] == SHAPE
                                and not seen[nr][nc]):
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(cells)

    T = {}
    for cells in comps:
        rgn = region[cells[0][0]][cells[0][1]]
        minc = min(c for _, c in cells)
        maxc = max(c for _, c in cells)
        if rgn == 8:
            shift = cols[8][0] - minc          # slide to region's left edge
        else:
            shift = cols[1][1] - maxc          # slide to region's right edge
        for (cr, cc) in cells:
            T[(cr, cc)] = ('bg', rgn)          # erase old shape cell to bg
        for (cr, cc) in cells:
            T[(cr, cc + shift)] = ('shape', SHAPE)  # paint shifted shape cell
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), (kind, col) in T.items():
        if kind == 'bg':
            out[r][c] = col
    for (r, c), (kind, col) in T.items():
        if kind == 'shape':
            out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
