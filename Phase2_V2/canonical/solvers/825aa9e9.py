from collections import Counter


def _detect_colors(grid):
    """Return (bg, struct, obj) colors, or None if the 3-color layout is absent.

    bg     : the background field color (objects float in it)
    struct : the floor / ground color objects come to rest above
    obj    : the falling object color
    """
    H = len(grid)
    W = len(grid[0])
    cnt = Counter(v for row in grid for v in row)
    if len(cnt) < 3:
        return None
    bottom = set(grid[H - 1])
    # The object color floats above the floor, so it never reaches the bottom
    # row; among such colors it is the least frequent.
    nonbottom = [c for c in cnt if c not in bottom]
    if not nonbottom:
        return None
    obj = min(nonbottom, key=lambda c: cnt[c])
    others = [c for c in cnt if c != obj]
    if len(others) != 2:
        return None
    # The object shapes sit in a sea of background, so the background is the
    # color most 8-adjacent to the object; the remaining color is the floor.
    adj = Counter()
    for r in range(H):
        for c in range(W):
            if grid[r][c] == obj:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        a, b = r + dr, c + dc
                        if 0 <= a < H and 0 <= b < W and grid[a][b] != obj:
                            adj[grid[a][b]] += 1
    bg = max(others, key=lambda c: adj[c])
    struct = next(c for c in others if c != bg)
    return bg, struct, obj


def _components(grid, color):
    """8-connected components of `color`, each a list of (r, c)."""
    H = len(grid)
    W = len(grid[0])
    seen = set()
    out = []
    nb = ((1, 0), (-1, 0), (0, 1), (0, -1),
          (1, 1), (1, -1), (-1, 1), (-1, -1))
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] != color:
                        continue
                    seen.add((a, b))
                    cells.append((a, b))
                    for dr, dc in nb:
                        stack.append((a + dr, b + dc))
                out.append(cells)
    return out


def infer_T(input_grid):
    """Latent mask: drop each object shape under gravity until it rests one cell
    above the floor (the structural color or the grid bottom); shapes stack
    flush against one another. T maps every changed cell to its new color
    (background where an object left, object color where it landed)."""
    H = len(input_grid)
    W = len(input_grid[0])
    det = _detect_colors(input_grid)
    if det is None:
        return {}
    bg, struct, obj = det
    structcells = set((r, c) for r in range(H) for c in range(W)
                      if input_grid[r][c] == struct)

    comps = _components(input_grid, obj)
    # settle the lowest shapes first so higher ones can stack on them
    comps.sort(key=lambda cs: -max(r for r, c in cs))

    occupied = set()  # cells taken by already-settled object shapes
    landed = []
    for cells in comps:
        k = 0
        while True:
            nk = k + 1
            hit_floor = any((r + nk) >= H or (r + nk, c) in structcells
                            for r, c in cells)
            hit_obj = any((r + nk, c) in occupied for r, c in cells)
            if hit_floor:
                # nk overlaps the floor, nk-1 touches it, nk-2 leaves a 1 gap
                k = nk - 2
                break
            if hit_obj:
                # rest flush on top of the shape below
                k = nk - 1
                break
            k = nk
        moved = [(r + k, c) for r, c in cells]
        for cell in moved:
            occupied.add(cell)
        landed.append(moved)

    T = {}
    # clear the old object footprint to background
    for cells in comps:
        for r, c in cells:
            T[(r, c)] = bg
    # paint the settled shapes
    for cells in landed:
        for r, c in cells:
            if 0 <= r < H and 0 <= c < W:
                T[(r, c)] = obj
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
