def _components(cells):
    """8-connected connected components over a set of (r, c) cells."""
    cells = set(cells)
    seen = set()
    out = []
    for s in cells:
        if s in seen:
            continue
        stack = [s]
        comp = []
        while stack:
            x = stack.pop()
            if x in seen or x not in cells:
                continue
            seen.add(x)
            comp.append(x)
            r, c = x
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr or dc:
                        stack.append((r + dr, c + dc))
        out.append(comp)
    return out


def infer_T(input_grid):
    """Latent transformation mask: a full {(r, c): color} grid.

    Structure of the input:
      * a "box": a 3x3 ring of color 4 (8 ring cells) with a single center
        cell of some color C (the box's center color);
      * a "snake": a short path with one endpoint colored C and one cell
        colored 4. The displacement from the C endpoint to the 4 cell is a
        translation vector.

    Output rule:
      * the whole grid is repainted with the background color C;
      * the 3x3 box (ring 4 / center C) is redrawn, translated by the snake
        vector;
      * four diagonal rays of color 4 shoot outward from the box's four outer
        corners, each running straight until it leaves the grid (no reflection).
    """
    H, W = len(input_grid), len(input_grid[0])
    g = input_grid
    nz = [(r, c) for r in range(H) for c in range(W) if g[r][c] != 0]
    comps = _components(nz)

    # Locate the box (3x3, eight color-4 ring cells).
    box = None
    for comp in comps:
        if len(comp) == 9 and sum(1 for (r, c) in comp if g[r][c] == 4) == 8:
            box = comp
            break
    if box is None:
        return {}
    rs = [r for r, c in box]
    cl = [c for r, c in box]
    br = (min(rs) + max(rs)) // 2
    bc = (min(cl) + max(cl)) // 2
    C = g[br][bc]  # box center color == output background color

    # Locate the snake (contains a C cell and a 4 cell) and read its vector.
    snake = None
    for comp in comps:
        if comp is box:
            continue
        cset = set(g[r][c] for (r, c) in comp)
        if C in cset and 4 in cset:
            snake = comp
            break
    if snake is None:
        return {}
    cend = next((r, c) for (r, c) in snake if g[r][c] == C)
    four = next((r, c) for (r, c) in snake if g[r][c] == 4)
    dr, dc = four[0] - cend[0], four[1] - cend[1]

    # Translated box center.
    nbr, nbc = br + dr, bc + dc

    # Background everywhere.
    T = {}
    for r in range(H):
        for c in range(W):
            T[(r, c)] = C

    # Redraw the 3x3 box at the translated position.
    for ddr in (-1, 0, 1):
        for ddc in (-1, 0, 1):
            rr, cc = nbr + ddr, nbc + ddc
            if 0 <= rr < H and 0 <= cc < W:
                T[(rr, cc)] = C if (ddr == 0 and ddc == 0) else 4

    # Four diagonal rays from the outer corners of the box.
    for sdr in (-1, 1):
        for sdc in (-1, 1):
            rr, cc = nbr + 2 * sdr, nbc + 2 * sdc
            while 0 <= rr < H and 0 <= cc < W:
                T[(rr, cc)] = 4
                rr += sdr
                cc += sdc

    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
