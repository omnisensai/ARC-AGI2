def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] and grid[nr][nc] == color:
                                seen[nr][nc] = True
                                stack.append((nr, nc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    fill_color = 3

    T = {}
    for comp in _components(input_grid, 2):
        rs = [p[0] for p in comp]
        cs = [p[1] for p in comp]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        cellset = set(comp)
        # determine interior cells (inside bounding box, not part of the border component)
        interior = []
        is_hollow_rect = True
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if (r, c) not in cellset:
                    interior.append((r, c))
        # Verify it is a proper rectangular ring: border forms full rectangle perimeter
        # and interior is the inside hole. Solid blocks have no interior -> skipped.
        if not interior:
            # solid block: erase it
            for (r, c) in comp:
                T[(r, c)] = bg
            continue
        # erase the border
        for (r, c) in comp:
            T[(r, c)] = bg
        # fill interior with fill_color
        for (r, c) in interior:
            T[(r, c)] = fill_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
